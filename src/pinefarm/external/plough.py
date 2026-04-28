"""Download grids + convert them to pineappl format."""

import os
import shutil
import tarfile
import urllib.request

import pineappl
import requests

from .. import table
from . import interface

PLOUGHSHARE_LINK_FILENAME = "ploughshare_link.txt"
GRIDS_TMP = "grids"


class Plough(interface.External):
    """Interface provider."""

    def __init__(self, pinecard, theorycard, *args, **kwargs):
        super().__init__(pinecard, theorycard, *args, **kwargs)
        self.ps_link = self.source / PLOUGHSHARE_LINK_FILENAME
        self.link = self.ps_link.read_text()

        self.filename = self.link.rsplit("/")[-1]
        self.dir_name = self.filename.rsplit(".", 1)[0]
        self.tarball = self.dest / self.filename
        self._print_comparison = False
        self._run_without_grids = True

    def run(self):
        """Download and extract the .tgz file."""
        print("Downloading from ploughshare...")
        try:
            self.download_to_dest()
            if self.tarball.exists():
                print(f"Grids successfully downloaded to {self.tarball}")
            else:
                raise FileNotFoundError(
                    f"{self.tarball} not found but the download didn't seem to fail?"
                )
        except Exception as e:
            raise FileNotFoundError(f"{self.tarball} could not be downloaded!") from e
        print("Extracting files...")
        self.extract_tarball()
        print(f"Grids successfully extracted to {self.dest}")

    def results(self):
        """Results are collected and compared at the pineappl (script) level."""
        pass

    def collect_versions(self):
        """No additional programs involved."""
        return {}

    def generate_pineappl(self):
        """Grids are converted in postrun.sh."""
        return

    def download_to_dest(self):
        """Download the file to the output folder."""
        urllib.request.urlretrieve(self.link, self.dest / self.filename)

    def extract_tarball(self):
        """Extract the contents."""
        with tarfile.open(self.tarball, "r:*") as tf:
            tf.extractall(self.dest)
        self.grids_dir = self.dest / self.dir_name / GRIDS_TMP
        grids_list = sorted(os.listdir(self.grids_dir))
        for i, grid in enumerate(grids_list):
            extension = grid.split(".", 2)[2]
            os.rename(self.grids_dir / grid, self.dest / f"grid_{i}.{extension}")
        shutil.rmtree(self.dest / self.dir_name)
        self.tarball.unlink()
