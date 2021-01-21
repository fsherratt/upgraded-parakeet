import datetime
import subprocess
import os
import time

from utils.__context import modules
from modules import realsense
from modules.utils import load_config

if __name__ == "__main__":
    # Load config file
    conf_file = "conf/realsense.yaml"
    log_folder = "logs/realsense_recordings"

    config = load_config.from_file(conf_file)
    config.realsense.record.record_to_file = True
    config.realsense.replay.load_from_file = False

    # Update record settings
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        os.makedirs(log_folder)
    except OSError as e:
        if e.errno != os.errno.EEXIST:
            raise

    log_folder = log_folder + "/" + timestamp
    try:
        os.makedirs(log_folder)
    except OSError as e:
        if e.errno != os.errno.EEXIST:
            raise

    device = "rs_depth"
    file_name = log_folder + "/" + device + "_log.bag"

    args_start = "python3 " "-m modules.realsense " "-p "
    args_end = (
        "--config_cli_override "
        "realsense.record.record_to_file=true "
        "realsense.replay.load_from_file=false "
        "realsense.record.log_file=" + log_folder + "/"
    )

    pDepth = subprocess.Popen(
        args_start + "rs_depth" + " --debug " + args_end + "rs_depth" + "_log.bag",
        shell=True,
    )
    pColor = subprocess.Popen(
        args_start + "rs_color" + " --debug " + args_end + "rs_color" + "_log.bag",
        shell=True,
    )
    pPose = subprocess.Popen(
        args_start + "rs_pose" + args_end + "rs_pose" + "_log.bag", shell=True,
    )
    print("Running process")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        pass
