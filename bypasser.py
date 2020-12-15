##########################################
Green="\033[1;33m"
Blue="\033[1;34m"
Grey="\033[1;30m"
Reset="\033[0m"
yellow="\033[1;36m"
Red="\033[1;31m"
purple="\033[35m"
Light="\033[95m"
cyan="\033[96m"
stong="\033[41m"
##########################################
import re
import time
import argparse
import threading
import subprocess
from threading import Timer
from multiprocessing.dummy import Pool

from config import *


def target_handle(target):
    if not target.startswith("https://"):
        target = "https://" + target
    return target


def is_alive():
    global target
    response = curl_request(target_handle(target), alive_command)
    if response is None or response == "":
        return False
    else:
        return True


def curl_request(target, command, timeout=15):
    execute = subprocess.Popen("{} {}".format(command, target), shell=False, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    timer = Timer(timeout, execute.kill)
    try:
        timer.start()
        stdout, stderr = execute.communicate()
        return stdout
    except:
        return None
    finally:
        timer.cancel()


def get_supported_ciphers():
    global target
    ciphers = []
    body = curl_request(target, ciphers_command, timeout=60)
    for line in str(body).split("\n"):
        match = re.findall("(Accepted|Preferred)\s+(.*?)\s+(.*?)\s+bits\s+(.*)", line.strip())
        if match:
            ciphers.append(match[0][3])
    return ciphers


def single_cipher_request(cipher):
    global target, count, base_length, cipher_content_length
    count = 0
    cipher_response = curl_request(target + payload_request, "{} {}".format(curl_command, "--cipher " + cipher))
    mutex.acquire()
    if enable_waf_keyword:
        if not re.findall(hit_waf_regex, cipher_response):
            if len(cipher_response) == 0:
                count += 1
                print("[+] Cipher:{:35} Response Length: [0]".format(cipher))
            else:
                print("[+] Success! Find Bypass Cipher: {}".format(cipher))
                exit("[+] Please Test: [{}]".format("{} {}".format(curl_command, "--cipher " + cipher + " " +
                                                                  target + payload_request)))
        else:
            count += 1
            print("[-] Cipher:{:35} Filter By Waf!".format(cipher))
    else:
        cipher_length = len(cipher_response)
        if base_length != cipher_length:
            cipher_content_length.append({cipher: cipher_length})
            print("[+] Cipher:{:35} Response Length: [{}]".format(cipher, cipher_length))
        elif cipher_length == 0:
            print("[+] Cipher:{:35} Response Length: [0]".format(cipher))
        else:
            count += 1
            print("[+] Cipher:{:35} Response Length: [Same as Base Response]".format(cipher))
    mutex.release()


def bypass_testing(threads=1):
    global target, base_length
    if is_alive():
        print("[+] Target: {} is alive".format(target))
    else:
        exit("[-] Target: {} cannot connected".format(target))

    print("[+] Testing Web Server Supported SSL/TLS Ciphers ...")
    ciphers = get_supported_ciphers()
    if len(ciphers) > 0:
        print("[+] {} Supported [{}] SSL/TLS Ciphers".format(target, len(ciphers)))
    else:
        print("[-] No SSL/TLS Ciphers of target supported")

    base_content_1 = curl_request(target, curl_command)
    base_content_2 = curl_request(target + normal_request, curl_command)
    if len(base_content_1) == len(base_content_2):
        base_length = len(base_content_1)
        print("[!] Response-1 == Response-2 length:[{}]".format(len(base_content_1)))
    else:
        base_length = len(base_content_2)
        print("[+] Request-1:{}  Request-2:{}".format(target, target + normal_request))
        print("[!] Response-1 length:[{}]  !=  Response-2 length:[{}]".format(len(base_content_1), len(base_content_2)))

    print("[+] Now Request: {}".format(target + payload_request))

    if threads > 1:
        pool = Pool(threads)
        pool.map(single_cipher_request, ciphers)
        pool.close()
        pool.join()
    else:
        for cipher in ciphers:
            single_cipher_request(cipher)

    if not enable_waf_keyword:
        bcl_count = 0
        base_cipher_length = dict(cipher_content_length[0]).values()[0]
        for d in cipher_content_length:
            if dict(d).values()[0] == base_cipher_length:
                bcl_count += 1
    else:
        bcl_count = -1
    if count == len(ciphers) or bcl_count == len(ciphers):
        print("[-] Failed! Abusing SSL/TLS Ciphers Cannot Bypass Waf")
    else:
        print("[*] Finished! Please check response content length and find whether there is bypass way")

print("        "+purple+"MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+purple+"MMMMMMMMMMNKWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+purple+"MMMMMMMMMNc.dWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Blue+"MMMMMMMMWd. .kWMMMMMMMMMMMMMMMMMMMMMMW0KMMMMMMMMMM")
print("        "+Blue+"MMMMMMMMk:;. 'OMMMMMMMMMMMMMMMMMMMMMWx.,0MMMMMMMMM")
print("        "+Blue+"MMMMMMMK:ok.  ,0MMMMMMMMMMMMMMMMMMMWO. .cXMMMMMMMM")
print("        "+Blue+"MMMMMMNl:KO.   ;KWNXK00O0000KXNWMMWO' .c;dWMMMMMMM")
print("        "+Blue+"MMMMMMx,xNk.    .;'...    ....';:l:.  ,0l,0MMMMMMM")
print("        "+Blue+"MMMMMK;,l;. .,:cc:;.                  .dx,lWMMMMMM")
print("        "+Blue+"MMMMWo    ,dKWMMMMWXk:.      .cdkOOxo,. ...OMMMMMM")
print("        "+Blue+"MMMM0'   cXMMWKxood0WWk.   .lkONMMNOOXO,   lWMMMMM")
print("        "+Blue+"MMMWl   ;XMMNo.    .lXWd. .dWk;;dd;;kWM0'  '0MMMMM")
print("        "+Blue+"kxko.   lWMMO.      .kMO. .OMMK;  .kMMMNc   oWMMMM")
print("        "+Blue+"X0k:.   ;KMMXc      :XWo  .dW0c,lo;;xNMK,   'xkkk0")
print("        "+Blue+"kko'     :KMMNkl::lkNNd.   .dkdKWMNOkXO,    .lOKNW")
print("        "+Blue+"0Kk:.     .lOXWMMWN0d,       'lxO0Oko;.     .ckkOO")
print("        "+Blue+"kkkdodo;.    .,;;;'.  .:ooc.     .        ...ck0XN")
print("        "+Blue+"0XWMMMMWKxc'.          ;dxc.          .,cxKK0OkkOO")
print("        "+Blue+"MMMMMMMMMMMN0d:'.  .'        .l'  .;lxKWMMMMMMMMMN")
print("        "+Blue+"MMMMMMMMMMMMMMMN0xo0O:,;;;;;;xN0xOXWMMMMMMMMMMMMMM")
print("        "+Red+"MMMMMMMMMMMMMMMMMMMMMMWWWWWMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Red+"MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Red+"MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Red+"MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Red+"MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Blue+"              "+Green+"["+Reset+"ByPasser"+Reset+"]"+Blue+"         ")
print("     "+purple+"         "+purple+"["+Light+"  Created By ybenel"+Light+"]"+purple+"    "+Reset+"\n")

if __name__ == "__main__":
    start = time.time()
    parser = argparse.ArgumentParser(prog='bypasser.py')
    parser.add_argument("-regex", dest='regex', default='default', help="hit waf keyword or regex")
    parser.add_argument("-thread", dest='thread', default=1, type=int, help="numbers of multi threads")
    parser.add_argument("-target", dest='target', default='default', help="the host ip or domain")

    if len(sys.argv) == 1:
        sys.argv.append('-h')
    args = parser.parse_args()
    if args.regex != 'default':
        enable_waf_keyword = True
        hit_waf_regex = args.regex

    count = 0
    base_length = 0
    target = target_handle(args.target)
    cipher_content_length = []
    mutex = threading.Lock()
    bypass_testing(int(str(args.thread)))
    print("[+] Cost: {:.6} seconds".format(time.time() - start))
