import os
import shutil
import logging
import datetime
from time import sleep
import cv2
from imutils.video import VideoStream
from flask import Flask, render_template, Response
from multiprocessing import Process


class YiCam:

    def __init__(self):
        """
        Create and initialize instance of the class.
        """

        # Define object variables with environment variables
        self.user = os.environ.get("CAM_USER", None)
        self.password = os.environ.get("CAM_PASSWORD", None)
        self.cam_ip = os.environ.get("CAM_IP", None)
        # self.cam_port = os.environ.get("CAM_PORT", None)

        # Make sure needed variables are defined
        assert self.user is not None
        assert self.password is not None
        assert self.cam_ip is not None
        # assert self.cam_port is not None

        # Create the url to the camera rtsp stream
        self.cam_rstp = "rtsp://%s:%s@%s/ch0_0.h264" % (
            self.user, self.password, self.cam_ip)
        self.stream = VideoStream(self.cam_rstp).start()

    def capture_image(self):
        """
        Save an image from the rtsp to the corresponding folder
        """
        frame = self.stream.read()
        # cv2.imshow("Test", frame)
        return frame

    def save_image(self, frame, filepath):
        cv2.imwrite(filepath, frame)
        return True

    def stop(self):
        self.stream.stop()

    def gen_frames(self):
        while True:
            frame = self.capture_image()
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def create_needed_folders(data_folder: str, retention_period: int):
    now = datetime.datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")

    year_path = "%s/%s" % (data_folder, year)
    month_path = "%s/%s" % (year_path, month)
    day_path = "%s/%s" % (month_path, day)

    try:
        for path in [year_path, month_path, day_path]:
            if not os.path.exists(path):
                os.mkdir(path)
            if path == day_path:
                try:
                    delete_mandatory(now, retention_period)
                except Exception as e:
                    logging.debug("Couldn't delete directory")
                    logging.debug(e)
        return day_path
    except Exception as e:
        logging.error(e)
        logging.error("Couldn't create the directories")
        return False


def delete_mandatory(now, retention_period: int):
    to_delete = now - datetime.timedelta(days=retention_period)
    to_delete_year = to_delete.strftime("%Y")
    to_delete_month = to_delete.strftime("%m")
    to_delete_day = to_delete.strftime("%d")

    to_delete_year_path = "%s/%s" % (data_folder,
                                     to_delete_year)
    to_delete_month_path = "%s/%s" % (to_delete_year_path,
                                      to_delete_month)
    to_delete_day_path = "%s/%s" % (
        to_delete_month_path, to_delete_day)
    shutil.rmtree(to_delete_day_path)
    if len(os.listdir(to_delete_month_path)) == 0:
        shutil.rmtree(to_delete_month_path)
    if len(os.listdir(to_delete_year_path)) == 0:
        shutil.rmtree(to_delete_year_path)


# Only run the following code if not imported from another module
if __name__ == "__main__":

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Configure the interval in seconds between images
    interval = int(os.environ.get("INTERVAL", 5))

    retention_period = int(os.environ.get("RETENTION_PERIOD", 30))

    # Configure data folder path
    data_folder = os.environ.get('DATA_FOLDER', None)
    assert data_folder is not None

    app = Flask(__name__)

    # Create camera instance
    cam = YiCam()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/video_feed')
    def video_feed():
        return Response(cam.gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    def run():
        # Capture image every X seconds
        while True:

            img = cam.capture_image()
            filepath = create_needed_folders(data_folder, retention_period)
            if filepath is False:
                continue
            filename = datetime.datetime.now().strftime("%H:%M:%S")
            file = f"{filepath}/{filename}.jpeg"
            logging.info(file)
            cam.save_image(img, file)
            # key = cv2.waitKey(1) & 0xFF
            # if key == ord('q'):
            #     break
            sleep(interval)

        cam.stop()

    p = Process(target=run)
    p.start()

    app.run(port=8000, debug=True)
