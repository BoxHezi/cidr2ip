#!/usr/local/bin/python3

import os
import argparse
import ipaddress
import pickle
from tqdm import tqdm

import git

GIT_LOCAL_REPO = "country-ip-blocks"
GIT_REMOTE_URL_SSH = "git@github.com:herrbischoff/country-ip-blocks.git"
GIT_REMOTE_URL_HTTPS = "https://github.com/herrbischoff/country-ip-blocks.git"

BASE_PATH = "./country-ip-blocks/ipv4/"

parser = argparse.ArgumentParser(prog="cidr2ip",
                                 description="CIDR to IPs, get CIDR from https://github.com/herrbischoff/country-ip"
                                             "-blocks.git",
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-c", "--country",
                    help="country code\naccept multiple country code, separate using space.\nExample: -c au us nz. "
                         "Default country code: au for australia",
                    default=["au"], type=str, nargs="+")
parser.add_argument("-r", "--rerun", help="Ignore update check, rerun all cidr to ip based on given country code.",
                    action="store_true")

args = parser.parse_args()
print(args.country)


# init phase, if not clone yet, clone to local
def init():
    if not os.path.exists(GIT_LOCAL_REPO):
        git.Repo.clone_from(GIT_REMOTE_URL_SSH, GIT_LOCAL_REPO)

    return git.Repo(GIT_LOCAL_REPO)


# check if git repo has update
def check_update(repo: git.Repo):
    origin = repo.remotes.origin
    origin.fetch()

    local_hash = repo.head.commit.hexsha
    remote_hash = origin.refs.master.commit.hexsha

    if local_hash == remote_hash:
        print("Up to date")
        return False
    else:
        print("Git Repo Updated Detected")
        print("Pulling from remote...")
        origin.pull()
        return True


def check_ipv4(code):
    path = BASE_PATH + code + ".cidr"
    cidrs = {}
    with open(path, "r") as reader:
        print("Start parsing IPv4 cidr for country code {}...".format(code.replace(".cidr", "").capitalize()))
        lines = [line.strip() for line in reader]
        for cidr in tqdm(lines):
            # using python ipaddress library
            cidrs[cidr] = [str(ip) for ip in ipaddress.IPv4Network(cidr)]

            # using mapcidr made by projectdiscovery
            # https://github.com/projectdiscovery/mapcidr
            # result = subprocess.run(["mapcidr", "-cl", cidr, "-t4", "-silent"], capture_output=True)
            # result = result.stdout.decode().rstrip()
            # cidrs[cidr] = result.split("\n")

    return cidrs


def check_ipv6(code):
    path = BASE_PATH + code + ".cidr"
    cidrs = {}
    with open(path, "r") as reader:
        print("Start parsing IPv6 cidr for country code {}...".format(code.replace(".cidr", "").capitalize()))
        lines = [line.strip() for line in reader]
        for cidr in tqdm(lines):
            cidrs[cidr] = [str(ip) for ip in ipaddress.IPv6Network(cidr)]

    return cidrs


def main():
    repo = init()

    if args.rerun or check_update(repo):
        for code in args.country:
            data = check_ipv4(code)

            pickle_name = code + ".data.pickle"
            with open(pickle_name, "wb") as file:
                pickle.dump(data, file)

    repo.close()


main()
