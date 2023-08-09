#!/usr/local/bin/python3

import os
import sys
import argparse
import ipaddress
import pickle
import subprocess
from tqdm import tqdm

import git

GIT_LOCAL_REPO = "country-ip-blocks"
GIT_REMOTE_URL_SSH = "git@github.com:herrbischoff/country-ip-blocks.git"
GIT_REMOTE_URL_HTTPS = "https://github.com/herrbischoff/country-ip-blocks.git"

parser = argparse.ArgumentParser(prog="cidr2ip"
                                 ,description="CIDR to IPs, get CIDR from https://github.com/herrbischoff/country-ip-blocks.git")
parser.add_argument("-c", "--country", help="country code\naccept multiple country code, separate using space.\nExample: -c au us nz. Default country code: au for australia", default=["au"], type=str, nargs="+")
parser.add_argument("-r", "--rerun", help="Ignore update check, rerun all cidr to ip based on given country code.", action="store_true")

args = parser.parse_args()
print(args.country)

# init phase, if not clone yet, clone to local
def init():
    if not os.path.exists(GIT_LOCAL_REPO):
        git.Repo.clone_from(GIT_REMOTE_URL_SSH, GIT_LOCAL_REPO)

    return git.Repo(GIT_LOCAL_REPO)

# check if git repo has update
def checkUpdate(repo: git.Repo):
    origin = repo.remotes.origin
    origin.fetch()

    localHash = repo.head.commit.hexsha
    remoteHash = origin.refs.master.commit.hexsha

    if localHash == remoteHash:
        print("Up to date")
        return False
    else:
        print("Git Repo Updated Detected")
        print("Pulling from remote...")
        origin.pull()
        return True

def checkIPv4(code):
    PATH = "./country-ip-blocks/ipv4/" + code + ".cidr"
    cidrs = {}
    with open(PATH, "r") as reader:
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


def checkIPv6(code):
    PATH = "./country-ip-blocks/ipv6/" + code + ".cidr"
    cidrs = {}
    with open(PATH, "r") as reader:
        print("Start parsing IPv6 cidr for country code {}...".format(code.replace(".cidr", "").capitalize()))
        lines = [line.strip() for line in reader]
        for cidr in tqdm(lines):
            cidrs[cidr] = [str(ip) for ip in ipaddress.IPv6Network(cidr)]

    return cidrs

def main():
    repo = init()

    if args.rerun or checkUpdate(repo):
        for code in args.country:
            data = checkIPv4(code)

            picklename = code + ".data.pickle"
            with open(picklename, "wb") as file:
                pickle.dump(data, file)


    repo.close()

main()

