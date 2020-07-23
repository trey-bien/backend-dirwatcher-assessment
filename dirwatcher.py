import argparse
import sys
import os
import logging
import time
import signal
import errno
from datetime import datetime as dt

__author__ = "Trey Dickerson"

logger = logging.getLogger(__name__)

exit_flag = False

def signal_handler(sig_num, frame):
    """
    This is a handler for SIGTERM and SIGINT.  Other signals can be mapped here as well (SIGHUP?)
    Basically it just sets an event, and main() will exit it's loop when the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """
    logger.warn('Received OS process signal {}'.format(sig_num))
    global exit_flag

    if sig_num == signal.SIGINT or sig_num == signal.SIGTERM:
        exit_flag = True


def find_magic(obj, start, magic_string):

    obj.seek(start[0])
    line_num = start[1]
    for line_num, line in enumerate(obj, start[1]):
        if magic_string in line:
            logger.info('Match on line {}: {}'.format(line_num, line.strip()))
    return obj.tell(), line_num


def watch_dir(path, magic_string, ext, interval):

    def file_dict():
        abs_path = os.path.abspath(path)
        return dict([(os.path.join(abs_path, f), (0, 1)) for f in os.listdir(abs_path)])

    a = file_dict()
    while not exit_flag:
        b = file_dict()
        added = [f for f in b if f not in a]
        removed = [f for f in a if f not in b]
        time.sleep(interval)
        if added:
            logger.info('File(s) added: {}'.format(', '.join(added)))
        if removed:
            logger.info('File(s) removed: {}'.format(', '.join(removed)))
        for f in b:
            if f.endswith(ext):
                with open(f) as fo:
                    b[f] = find_magic(fo, a[f], magic_string)
        a = b


def main():

    parser = argparse.ArgumentParser(
        description='Watches a directory of text files for a magic string')
    parser.add_argument('-e', '--ext', type=str, default='.txt',
                        help='Text file extension to watch e.g. .txt, .log')
    parser.add_argument('-i', '--interval', type=float,
                        default=1.0, help='Number of seconds between polling')
    parser.add_argument('path', help='Directory path to watch')
    parser.add_argument('magic', help='String to watch for')
    args = parser.parse_args()


    if not args:
        parser.print_usage()
        sys.exit(1)

    app_start_time = dt.now()

    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s [%(threadName)-12s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger.setLevel(logging.DEBUG)

    logger.info(
        '\n'
        '-------------------------------------------------------------------\n'
        '    Running {0}\n'
        '    Started on {1}\n'
        '-------------------------------------------------------------------\n'
        .format(__file__, app_start_time.isoformat())
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while not exit_flag:

        try:
            watch_dir(args.path, args.magic, args.ext, args.interval)

        except OSError as e:
            if e.errno == errno.ENOENT:
                logger.error(
                    'Directory not found: {}'.format(os.path.abspath(args.path)))
            else:
                logger.error(e)
            time.sleep(5.0)
            continue

        except Exception as e:
            error_str = 'Unhandled Exception in MAIN\n{}\nRestarting ...'.format(
                str(e))
            logger.error(error_str, exc_info=True)
            time.sleep(5.0)
            continue

    uptime = dt.now() - app_start_time
    logger.info(
        '\n'
        '-------------------------------------------------------------------\n'
        '   Stopped {0}\n'
        '   Uptime {1}\n'
        '-------------------------------------------------------------------\n'
        .format(__file__, str(uptime)))

    logging.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())