import argparse
import csv
import json
import logging
import os
import re
from subprocess import Popen, PIPE
from urllib.parse import urlparse

import requests

SFX_EXTS = {'.wav', '.mp3', '.mp4', '.ogg', '.m4a', '.flac'}
NORMALIZE_PARAMS = {
    "output_i": "-16",
    "output_tp": "-1.5",
    "output_lra": "11",
}


def download_sfx(args):
    with open(args.file, newline='') as f:
        reader = csv.reader(f)
        first = True
        for row in reader:
            if first and not args.no_header:
                first = False
                continue

            try:
                group, title, url = row
                parsed_url = urlparse(url)

                # get extension
                _, raw_ext = os.path.splitext(parsed_url.path)
                if raw_ext.lower() in SFX_EXTS:
                    ext = raw_ext.lower()
                else:
                    ext = ".wav"

                out_path = os.path.join(args.out_dir, "{} - {}{}".format(group, title, ext))
                exists = os.path.exists(out_path)

                if exists and not args.overwrite:
                    logging.info("already exists: {} (use --overwrite)".format(out_path))
                else:
                    logging.info("downloading to {}".format(out_path))
                    r = requests.get(url)
                    with open(out_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
            except Exception as e:
                logging.exception("failed to process row")


def normalize_sfx(args):
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)

    for file in os.listdir(args.in_dir):
        in_path = os.path.join(args.in_dir, file)

        # is it even a file?
        if not os.path.isfile(in_path):
            continue

        # is an audio file?
        _, ext = os.path.splitext(file)
        if not ext.lower() in SFX_EXTS:
            continue

        out_path = os.path.join(args.out_dir, file)
        exists = os.path.exists(out_path)

        if exists and not args.overwrite:
            logging.info("already exists: {} (use --overwrite)".format(out_path))
        else:
            logging.info("normalizing to {}...".format(out_path))

            # first pass
            p = Popen(
                ['ffmpeg', '-i', in_path, '-af', 'loudnorm=I={output_i}:TP={output_tp}:LRA={output_lra}:print_format=json'.format(**NORMALIZE_PARAMS), '-f', 'null', '-'],
                stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()

            if p.returncode != 0:
                logging.error(
                    "failed to get params for normalization:\n\n{}".format(stderr.decode('utf-8', errors='ignore')))
                continue

            r = re.search("(\\{[^{]+)$", stderr.decode('utf-8'))
            params = json.loads(r.group(1))
            params.update(NORMALIZE_PARAMS)

            # normalize
            p = Popen(['ffmpeg', '-y', '-i', in_path, '-af',
                       'loudnorm=I={output_i}:TP={output_tp}:LRA={output_lra}:measured_I={input_i}:measured_LRA={input_lra}:'
                       'measured_TP={input_tp}:measured_thresh={input_thresh}:offset={target_offset}:'
                       'linear=true:print_format=summary'.format(**params), '-ar', '48k', out_path],
                      stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()

            if p.returncode != 0:
                logging.error("failed to normalize:\n\n{}".format(stderr.decode('utf-8', errors='ignore')))
                continue


def main():
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
    logging.getLogger('requests').setLevel(logging.WARNING)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='action')
    subparsers.required = True

    subparser = subparsers.add_parser('download')
    subparser.set_defaults(func=download_sfx)
    subparser.add_argument('--no-header', action='store_true')
    subparser.add_argument('--overwrite', action='store_true')
    subparser.add_argument('file')
    subparser.add_argument('out_dir')

    subparser = subparsers.add_parser('normalize')
    subparser.set_defaults(func=normalize_sfx)
    subparser.add_argument('--overwrite', action='store_true')
    subparser.add_argument('in_dir')
    subparser.add_argument('out_dir')

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
