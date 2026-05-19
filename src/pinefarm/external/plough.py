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
GRIDS_FROM_PS = "grids"
PLOUGHSHARE_METADATA_LINK = (
    "https://ploughshare.web.cern.ch/ploughshare/record.php?group="
)
DATASET_FOR_METADATA_LINK = "&dataset="


class Plough(interface.External):
    """Interface to download grids directly from ploughshare."""

    def __init__(self, pinecard, theorycard, *args, **kwargs):
        super().__init__(
            pinecard,
            theorycard,
            *args,
            print_comparison=False,
            postrun_without_grids=True,
            **kwargs,
        )
        self.ps_link = self.source / PLOUGHSHARE_LINK_FILENAME
        self.link = self.ps_link.read_text()

        self.filename = self.link.rsplit("/")[-1]
        self.ploughshare_id = self.filename.rsplit(".", 1)[0]
        self.tarball = self.dest / self.filename
        self.group = self.ploughshare_id.split("-", 1)[0]
        self.ploughshare_metadata_link = (
            PLOUGHSHARE_METADATA_LINK
            + self.group
            + DATASET_FOR_METADATA_LINK
            + self.ploughshare_id
        )

    def run(self):
        """Download and extract the .tgz file."""
        print("Downloading from ploughshare...")
        self.download_to_dest()
        print("Extracting files...")
        self.extract_tarball()
        print(f"Grids successfully extracted to {self.dest}")

    def results(self):
        """Do nothing."""
        pass

    def collect_versions(self):
        """No additional programs involved."""
        return {}

    def generate_pineappl(self):
        """Grids are converted in postrun.sh."""
        return

    def download_to_dest(self):
        """Download the file to the output folder."""
        try:
            urllib.request.urlretrieve(self.link, self.dest / self.filename)
            if self.tarball.exists():
                print(f"Grids successfully downloaded to {self.tarball}")
            else:
                raise FileNotFoundError(
                    f"{self.tarball} not found but the download didn't seem to fail?"
                )
        except Exception as e:
            raise FileNotFoundError(f"{self.tarball} could not be downloaded!") from e

    def extract_tarball(self):
        """Extract the contents."""
        with tarfile.open(self.tarball, "r:*") as tf:
            tf.extractall(self.dest)
        self.grids_dir = self.dest / self.ploughshare_id / GRIDS_FROM_PS
        grids_list = sorted(os.listdir(self.grids_dir))
        for grid in grids_list:
            grid_num, extension = grid.split(".", 2)[1:]
            grid_num = grid_num[-3:]
            os.rename(self.grids_dir / grid, self.dest / f"grid_{grid_num}.{extension}")
        shutil.rmtree(self.dest / self.ploughshare_id)
        self.tarball.unlink()
