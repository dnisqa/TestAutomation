'''
    Description: This script is used to load SONIC image
    Requirement:
        Need console server to connect the console port of device.
        The management port of device connects http server.
    Parameter:
        --build_ver: code build number
        --console_ip : console server ip
        --console_port : telnet port number
        --http_ip : http server ip address
        --image : image name
        --mgmt_interface : management interface
        --mgmt_ip : management port ip address
        --mgmt_mask : management port ip mask
        --gw_ip : management port gateway ip address
        --fileweb_ip : file web server ip and conf path
        --dug_cfg : DUT default json cfg (filename)

    example:
        python sonicimageLoader.py \
        --console_ip 192.168.2.251 \
        --console_port 1056 \
        --http_ip 192.168.2.37 \
        --image image_name \
        --mgmt_interface ma1 \
        --mgmt_ip 192.168.2.56 \
        --mgmt_mask 255.255.255.0 \
        --gw_ip 192.168.2.254 \
        --fileweb_ip 192.168.59.161/sonic/conf/ \
        --build_ver v280 \
        --dut_cfg cfg_9032v1default.json
'''

import pexpect
import sys
import time
import argparse

class ImageLoader():

    TERM_LENGTH_CMD = 'terminal length 0'
    SHOW_VERSION = 'uname -a'

    #--------------------------------------------------------------------
    # LOGIN
    #--------------------------------------------------------------------
    USER_NAME_PROMPT = 'Username:'
    DEF_USER_NAME = "admin"
    DEF_PASSWORD = "YourPaSsWoRd"
    SONIC_USER = "admin"
    SONIC_PASSWORD= "YourPaSsWoRd"
    #OS_LIST = ["onl","icos"]
    OS_LIST = ["onie","sonic"]
    OS_USER_NAME = [SONIC_USER,DEF_USER_NAME]
    OS_PASSWORD =  [SONIC_PASSWORD,DEF_PASSWORD]
    OS_choice = 0

#    HOSTNAME = 'localhost'
    HOSTNAME = "[-_\w]*"
    LAST_LOGIN = 'Last login:'
    #LOGIN_PROMPT = '[lL]ogin:'
    SONIC_DEF_LOGIN_PROMPT = 'sonic login:'
    SONIC_LOGIN_PROMPT = 'sonic-[\w] login:'
    #SONIC_LOGIN_PROMPT = 'sonic-(?is) login:'
    LOGIN_RETRY = 'Sorry, try again.'
    COMMAND_NOT_FOUND='command not found'
    SU_LOGIN_PROMPT = '\[sudo\] password for [\w]*:'
    USER_PROMPT = '[uU]ser:'
    PASSWORD_PROMPT = '[pP]assword:'
    LOGIN_INCORRECT='Login incorrect'

    NEW_LINE_CHARACTER = '\r\n'
    SHOW_RUN_CMD = 'show run'
    CLI_ERROR_MESSAGES = 'incorrect password attempts'
    USER_EXEC_MODE_PROMPT = '@[-\w_]*:[\w~/-]*#'
#    LOCALHOST_EXEC_MODE_PROMPT = HOSTNAME+':~#'

    #--------------------------------------------------------------------
    # SONIC Option
    #--------------------------------------------------------------------
    SONIC_LINUX_EXEC_MODE_PROMPT = '@[-\w_]*:[\w~/-]*\$'
    #SONIC_LINUX_Priv_MODE_PROMPT = '@[-\w_]*:[\w~/-]*\#'
    SONIC_PASSWORD_PROMPT = 'Password *'
    SONIC_SUDO_SU = 'sudo su'
    SONIC_WRITE_CHECK = 'Existing file will be overwritten, continue? [y/N]: '

    #--------------------------------------------------------------------
    # GRUB ONIE Option
    #--------------------------------------------------------------------
    GNU_GRUB = 'GNU GRUB'
    BOOTMENU='GNU GRUB'
    ONIE_PROMPT = r'ONIE:/\w* #'
    CHOOSE_OPTION_SONIC = r'\*SONiC-OS-HEAD'
    CHOOSE_OPTION_ONIE = r'\*ONIE *\|'
    CHOOSE_ONIE_INSTALL_OS = r'\*ONIE: Install OS'
    CHOOSE_ONIE_RESCUE = r'\*ONIE: Rescue'
    CHOOSE_ONIE_UNINSTALL_OS = r'\*ONIE: Uninstall OS'
    CHOOSE_ONIE_UPDATE_ONIE = r'\*ONIE: Update ONIE'
    CHOOSE_ONIE_EMBED_ONIE = r'\*ONIE: Embed ONIE'
    ONIE_SERVICE_DISCOVERY= r'Starting ONIE Service Discovery'
    NOS_INSTALL_FAILURE = r'NOS install unavailable in current ONIE mode'

    #--------------------------------------------------------------------
    # KEYS
    #--------------------------------------------------------------------
    KEY_UP = '\x1b[A'
    KEY_DOWN = '\x1b[B'
    KEY_RIGHT = '\x1b[C'
    KEY_LEFT = '\x1b[D'

    #--------------------------------------------------------------------
    TIMEOUT=120

    def __init__(self, device):

        self.console_ip = device["console_ip"]
        self.console_port = device["console_port"]
        self.http_ip = device["http_ip"]
        self.image = device["image"]
        self.build_ver = device["build_ver"]
        self.mgmt_interface = device["mgmt_interface"]
        self.mgmt_ip = device["mgmt_ip"]
        self.mgmt_mask = device["mgmt_mask"]
        self.gw_ip = device["gw_ip"]
        self.fileweb_ip = device["fileweb_ip"]
        self.dut_cfg = device["dut_cfg"]
        self.loadimage = False
#        self.loadimage = True

    def connect(self):

        if sys.version_info[0] == 3 :
            child = pexpect.spawn('telnet %s %s' % (self.console_ip, self.console_port),
                                    encoding='utf8',
                                    timeout = self.TIMEOUT)
        else:
            child = pexpect.spawn('telnet %s %s' % (self.console_ip, self.console_port),
                                    timeout = self.TIMEOUT)
        child.logfile_read = sys.stdout
        child.logfile_send = sys.stdout

        print("\n doing connect for test_debug_line1")

        self._prompt = self.USER_EXEC_MODE_PROMPT

        # To pass over the banner that comes before login prompt
        child.send(self.NEW_LINE_CHARACTER)
        retry=0

        print("\n doing connect for test_debug_line2")

        for j in range(50):
            try:
               i = child.expect([self.LAST_LOGIN,
                              self.SONIC_LOGIN_PROMPT,
                              self.SONIC_DEF_LOGIN_PROMPT,
                              self.PASSWORD_PROMPT,
                              self.USER_EXEC_MODE_PROMPT,
                              self.SONIC_LINUX_EXEC_MODE_PROMPT,
                              self.CHOOSE_OPTION_SONIC,
                              self.ONIE_SERVICE_DISCOVERY,
                              self.CHOOSE_ONIE_INSTALL_OS,
                              self.CHOOSE_ONIE_RESCUE,
                              self.CHOOSE_ONIE_UNINSTALL_OS,
                              self.CHOOSE_ONIE_UPDATE_ONIE,
                              self.CHOOSE_ONIE_EMBED_ONIE,
                              self.CHOOSE_OPTION_ONIE,
                              self.BOOTMENU,
                              self.ONIE_PROMPT,
                              self.NOS_INSTALL_FAILURE,
                              self.LOGIN_INCORRECT,
                              self.CLI_ERROR_MESSAGES,
                              self.SONIC_WRITE_CHECK,
                              pexpect.EOF,
                              pexpect.TIMEOUT],
                              timeout=self.TIMEOUT)
            except:
                print("Exception was thrown")
                print("debug information:")
                print(str(child))
#           print("\ni = %d",i)
            print("\n child.expect content: %s", str(child.expect))
            print("\n doing connect for test_debug_line3, i is %d", i)

            if i in [0]:
                # LAST_LOGIN
                child.send(self.NEW_LINE_CHARACTER)
            elif i in [1]:
                # SONIC_LOGIN_PROMPT
                time.sleep(2)
                child.sendline(self.OS_USER_NAME[self.OS_choice])
            elif i in [2]:
                # SONIC_DEF_LOGIN_PROMPT
                self.OS_choice = 1
                time.sleep(2)
                child.sendline(self.OS_USER_NAME[self.OS_choice])
            elif i in [3]:
                # PASSWORD_PROMPT
                time.sleep(1)
                child.sendline(self.OS_PASSWORD[self.OS_choice])
                if self.OS_choice == 1:
                    child.sendline(self.SONIC_SUDO_SU)
            elif i in [4]:
                # USER_EXEC_MODE_PROMPT
                child.send(self.NEW_LINE_CHARACTER)
                if not self.loadimage :
                    child.sendline("sudo -S reboot")
                else:
                    # configure management interface
                    child.sendline(format("sudo -S ifconfig %s down" %
                                          self.mgmt_interface))
                    child.sendline(format("sudo ifconfig %s %s netmask %s up" %
                                          (self.mgmt_interface,
                                           self.mgmt_ip,
                                           self.mgmt_mask)))
                    child.expect([self._prompt])
                    child.sendline("sudo route delete default")
                    child.expect([self._prompt])
                    child.sendline(format("sudo route add default gw %s %s" %
                                         (self.gw_ip,
                                          self.mgmt_interface)))
                    child.expect([self._prompt])
                    child.send(self.NEW_LINE_CHARACTER)
                    if self.OS_choice == 1 and self.loadimage:
                       #child.expect([self._prompt])
                       #cmd = "onie-nos-install" + " http://" + self.http_ip + "/" + self.image
                       cmda = "curl " + "http://" + self.fileweb_ip + self.dut_cfg + " -s -o " + self.dut_cfg
                       print("\nDownload Dut default config json: " + cmda)
                       child.sendline(cmda)
                       cmda = "curl " + "http://" + self.fileweb_ip + "autologout_time.sh" + " -s -o autologout_time.sh"
                       print("\nDownload Dut default setting 1 script: " + cmda)
                       child.sendline(cmda)
                       cmda = "curl " + "http://" + self.fileweb_ip + "clearlog_gz.sh" + " -s -o clearlog_gz.sh"
                       print("\nDownload Dut default setting 2 script: " + cmda)
                       child.sendline(cmda)
                       cmda = "curl " + "http://" + self.fileweb_ip + "sshd_mod.sh" + " -s -o sshd_mod.sh"
                       print("\nDownload Dut default setting 3 script: " + cmda)
                       child.sendline(cmda)
                       child.sendline(format("%s" %self.SONIC_SUDO_SU))
                       cmdb = "./" + "autologout_time.sh"
                       child.sendline(cmdb)
                       cmdb = "./" + "sshd_mod.sh"
                       child.sendline(cmdb)
                       cmdb = "./" + "clearlog_gz.sh"
                       child.sendline(cmdb)
                       cmdb = "sonic-cfggen -j " + self.dut_cfg + " --write-to-db & config save"
                       child.sendline(cmdb)
                       child.expect([self._prompt])
                    else:
                       break
            elif i in [5]:
                # SONIC_LINUX_EXEC_MODE_PROMPT
                if not self.loadimage:
                    child.sendline(format("sudo -S reboot"))
                    child.expect([self.BOOTMENU], timeout=600)
                else:
                    break
            elif i in [6]:
                # CHOOSE_OPTION_SONIC
                if not self.loadimage :
                    child.sendline(self.KEY_DOWN)
                else:
                    child.sendline(self.NEW_LINE_CHARACTER)
            elif i in [7]:
                # ONIE_SERVICE_DISCOVERY
                child.sendline(self.NEW_LINE_CHARACTER)
                child.sendline("onie-discovery-stop")
                child.sendline(self.NEW_LINE_CHARACTER)
            elif i in [8]:
                #CHOOSE_ONIE_INSTALL_OS
                child.sendline(self.NEW_LINE_CHARACTER)
            elif i in [9,10,11,12]:
                # CHOOSE_ONIE_RESCUE,
                # CHOOSE_ONIE_UNINSTALL_OS,
                # CHOOSE_ONIE_UPDATE_ONIE,
                # CHOOSE_ONIE_EMBED_ONIE,
                child.send(self.KEY_UP)
            elif i in [13]:
                # CHOOSE_OPTION_ONIE
                if not self.loadimage :
                    child.sendline(self.NEW_LINE_CHARACTER)
                else:
                    child.send(self.KEY_UP)
            elif i in [14]:
                # BOOTMENU
                continue
            elif i in [15]:
                # ONIE_PROMPT
                if not self.loadimage :
                    child.sendline("onie-discovery-stop")
                    child.expect([self.ONIE_PROMPT])
                    child.sendline("echo $boot_reason")
                    i = child.expect(["install",pexpect.EOF])
                    if i in [0]:
                        child.sendline("more /etc/machine.conf")
                        child.expect([self.ONIE_PROMPT])
                        cmd="onie-nos-install" + " http://" + self.http_ip + "/" + self.image + self.build_ver + "/" + "sonic-broadcom.bin"
                        print("\nLoading image : " + cmd)
                        child.sendline(cmd)
#                        child.sendline("reboot")
                        self.loadimage = True
                    else:
                        child.sendline("reboot")
                    child.expect([self.BOOTMENU],timeout = 600)
                else:
                    break
            elif i in [16]:
                # NOS_INSTALL_FAILURE
                child.sendline("reboot")
                child.expect([self.BOOTMENU],timeout = 600)
            elif i in [17]:
                # LOGIN_INCORRECT
#                child.send(self.NEW_LINE_CHARACTER)
                retry += 1
                print("OS= %s, retry = %d" % (self.OS_LIST[self.OS_choice],retry))
                if retry == 3:
                    if self.OS_choice == len(self.OS_LIST) - 1:
                        break
                    else:
                        self.OS_choice += 1
                        retry = 0
                else:
                    continue

            elif i in [18]:
                # CLI_ERROR_MESSAGES
                child.send(self.NEW_LINE_CHARACTER)
            elif i in [19]:
                # SONIC_WRITE_CHECK, put y to save config
                child.sendline("y")
                time.sleep(5)
                child.sendline("reboot")
                break
            elif i in [20]:
                # pexpect.TIMEOUT
                child.send(self.NEW_LINE_CHARACTER)
            else:
                child.send(self.NEW_LINE_CHARACTER)
                print("\nNo matching")
                break

        # Now we are in Linux prompt
        child.send(self.NEW_LINE_CHARACTER)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--console_ip", help="console IP address")
    parser.add_argument("--console_port", help="console port number")
    parser.add_argument("--http_ip", help="HTTP server IP address")
    parser.add_argument("--image", help="path/image")
    parser.add_argument("--build_ver", help="build number, ex: v280")
    parser.add_argument("--mgmt_interface", help="Management interface")
    parser.add_argument("--mgmt_ip", help="Management IP address")
    parser.add_argument("--mgmt_mask", help="Management IP mask")
    parser.add_argument("--gw_ip", help="Gateway IP address")
    parser.add_argument("--fileweb_ip", help="File Web server ip")
    parser.add_argument("--dut_cfg", help="Dut Default configuration json file")

    args = parser.parse_args()

    if args.console_ip and \
       args.console_port and \
       args.http_ip and \
       args.image:

        device = { "console_ip" : args.console_ip,
                   "console_port" : args.console_port ,
                   "http_ip"    : args.http_ip,
                   "image"      : args.image,
                   "build_ver"  : args.build_ver,
                   "mgmt_interface" : args.mgmt_interface,
                   "mgmt_ip"    : args.mgmt_ip,
                   "mgmt_mask"  : args.mgmt_mask,
                   "gw_ip"      : args.gw_ip,
                   "fileweb_ip" : args.fileweb_ip,
                   "dut_cfg"    : args.dut_cfg}
    else:

        device = { "console_ip" : "192.168.54.97",
                   "console_port" : "4000",
                   "http_ip"    : "192.168.59.161",
                   "image"      : "sonic/images/Deb9/",
                   "build_ver"  : "v280",
                   "mgmt_interface" : "ma1",
                   "mgmt_ip"    : "192.168.2.56",
                   "mgmt_mask"  : "255.255.255.0",
                   "gw_ip"      : "192.168.2.254",
                   "fileweb_ip" : "192.168.59.161/sonic/conf/",
                   "dut_cfg"    : "cfg_default.json"}

    print("%s %s %s %s %s %s %s %s %s %s %s" % (device["console_ip"],
                                       device["console_port"],
                                       device["http_ip"],
                                       device["image"],
                                       device["build_ver"],
                                       device["mgmt_interface"],
                                       device["mgmt_ip"],
                                       device["mgmt_mask"],
                                       device["gw_ip"],
                                       device["fileweb_ip"],
                                       device["dut_cfg"]))
    loader=ImageLoader(device)
    loader.connect()
