#!/usr/bin/python3
# -*- coding: utf-8 -*-
#

import sys, os, string
import urllib.request
import zipfile
import subprocess
from optparse import OptionParser


def call(cmd, **kwargs):
    print('Running: {0}'.format(' '.join(cmd)))
    return subprocess.call(cmd, **kwargs)


apk_file = ''
apk_folder = ''
project_name = ''
sign_file = ''
cwd = os.path.dirname(os.path.abspath(__file__))
home = os.path.dirname(os.path.realpath(sys.argv[0]))
outdir = None
external = "https://github.com/TheZ3ro/apk2java-linux/releases/download/tool/tool.zip"


def check_home(path):
    return os.path.isdir(path + "/tool")


def getunzipped(theurl, thedir, report):
    if not os.path.exists(thedir):
        os.mkdir(thedir)
    print("Downloading external tool... -> " + thedir + "/tool/")
    name = os.path.join(thedir, 'temp.zip')
    try:
        name, hdrs = urllib.request.urlretrieve(theurl, name, report)
    except IOError as e:
        print("Can't retrieve %r to %r: %s" % (theurl, thedir, e))
        return
    try:
        z = zipfile.ZipFile(name)
    except zipfile.error as e:
        print("Bad zipfile (from %r): %s" % (theurl, e))
        return
    for n in z.namelist():
        (dirname, filename) = os.path.split(n)
        perm = ((z.getinfo(n).external_attr >> 16) & 0x0777)
        if filename == '':
            # directory
            newdir = thedir + '/' + dirname
            if not os.path.exists(newdir):
                os.mkdir(newdir)
        else:
            # file
            fd = os.open(thedir + "/" + n, os.O_CREAT | os.O_WRONLY, perm)
            os.write(fd, z.read(n))
            os.close(fd)
    z.close()
    os.unlink(name)
    print("")


def report(blocknr, blocksize, size):
    current = blocknr * blocksize
    sys.stdout.write("\rProgress: {0:.2f}%".format(100.0 * current / size) + " - {0:.1f} MB".format(
        current / 1024 / 1024) + "/{0:.1f} MB".format(size / 1024 / 1024))


def print_header(text):
    block = "*********************************************"
    print(block)
    print('**' + text.center(len(block) - 4) + '**')
    print(block)


def apktool(smali):
    print_header('Extract, fix resource files')
    if apk_file != '':
        cmd = [home + '/tool/apktool_200rc3.jar', 'd', apk_file, '-o', outdir + project_name, '-f']

        if smali:
            cmd[-1] = '-sf'

        call(cmd)
        call(['mv', outdir + project_name + '/classes.dex', outdir + project_name + '/original/'])
    print('Done')


def dex2jar():
    print_header("Convert 'apk' to 'jar'")
    if apk_file != '':
        call([home + '/tool/dex2jar-0.0.9.15/d2j-dex2jar.sh', '-f', '-o', outdir + project_name + '.jar', apk_file])
        call([home + '/tool/dex2jar-0.0.9.15/d2j-asm-verify.sh', outdir + project_name + '.jar'])
        print('Done')


def procyon():
    print_header('Decompiling class files')
    if apk_file != '':
        call([home + '/tool/procyon-decompiler-0528.jar', '-jar', outdir + project_name + '.jar',
              '-o', outdir + project_name + '/src/'])
        print('Done')


def apktool_build():
    print_header('Building apk from smali')
    if apk_folder != '':
        call([home + '/tool/apktool_200rc3.jar', 'b', apk_folder, '-o', outdir + project_name + '-rebuild.apk'])
        global sign_file
        sign_file = outdir + project_name + '-rebuild.apk'
        print('Done')


def jar2jasmin():
    print_header("Convert 'jar' to 'jasmin'")
    if apk_file != '':
        call([home + '/tool/dex2jar-0.0.9.15/d2j-jar2jasmin.sh', '-f', '-o', outdir + project_name + '/jasmin',
              outdir + project_name + '.jar'])
        print('Done')


def jasmin_build():
    print_header('Build apk from jasmin')
    if apk_folder != '':
        call([home + '/tool/dex2jar-0.0.9.15/d2j-jasmin2jar.sh', '-f', '-o', outdir + project_name + '-new.jar',
              outdir + project_name + '/jasmin'])
        call([home + '/tool/dex2jar-0.0.9.15/d2j-asm-verify.sh', outdir + project_name + '-new.jar'])
        call([home + '/tool/dex2jar-0.0.9.15/d2j-jar2dex.sh', '-f', '-o', outdir + project_name + '/classes.dex',
              outdir + project_name + '-new.jar'])
        call(['zip', '-r ' + outdir + project_name + '-new.apk', '-j', outdir + project_name + '/classes.dex'])
        global sign_file
        sign_file = outdir + project_name + '-new.apk'
        print('Done')


def sign():
    print_header('Sign apk')
    call([home + '/tool/dex2jar-0.0.9.15/d2j-apk-sign.sh', '-f', '-o', outdir + project_name + '-signed.apk',
          sign_file])
    print('Done')


def main():
    global apk_folder, apk_file, project_name, home, outdir
    usage = "usage: %prog action file [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("--java", action="store_true", dest="java", default=True,
                      help="select java source format [DEFAULT]")
    parser.add_option("--smali", action="store_true", dest="smali", default=False, help="select smali source format")
    parser.add_option("--jasmin", action="store_true", dest="jasmin", default=False, help="select jasmin source format")
    parser.add_option("--no-source", action="store_true", dest="nosc", default=False, help="no source code generation")
    parser.add_option("-o", dest="outdir", default=cwd + "/", help="specify the output directory "
                                                                   + "(if not specified the decomipled version will be store in a folder in the script directory)")
    (options, args) = parser.parse_args()

    if home == cwd + "/apk2java":
        if check_home(home) == False:
            getunzipped(external, home, report)
    else:
        if check_home(home) == False:
            if check_home(cwd + "/apk2java") == False:
                getunzipped(external, cwd + "/apk2java", report)
                home = cwd + "/apk2java"
            else:
                home = cwd + "/apk2java"
    outdir = options.outdir

    if (options.smali + options.jasmin + options.nosc) > 1:
        print("[ ERROR ] You can only select 1 source format --[smali/jasmin/java/no-source]")
        exit(1)
    if len(args) == 2:
        if args[0] == 'd':
            if os.path.isfile(args[1]) and os.path.splitext(args[1])[-1].lower() == '.apk':
                apk_file = args[1]
                project_name = os.path.splitext(os.path.basename(args[1]))[0].lower()
                if not os.path.exists(outdir):
                    os.makedirs(outdir)

                call(["cp", apk_file, outdir + project_name + "-new.apk"])
                if options.jasmin == True:
                    dex2jar()
                    jar2jasmin()
                else:
                    apktool(options.smali)
                    if options.smali == False and options.nosc == False:
                        dex2jar()
                        procyon()
                call(["cp", tmp + project_name + "/", "./", "-R"])
            else:
                print("[ ERROR ] You must select a valid APK file!")
                exit(1)
        elif args[0] == 'b':
            if os.path.isdir(args[1]):
                apk_folder = args[1]
                project_name = os.path.basename(os.path.dirname(args[1]).lower())
                if options.jasmin == True:
                    jasmin_build()
                elif options.smali == True:
                    apktool_build()
                else:
                    print("[ ERROR ] Can't build apk with that source format. Only Jasmin or Smali supported")
                sign()
                call(["cp", sign_file, "./", ])
        else:
            parser.error("action can be only 'b' (build) or 'd' (decompile)")
    else:
        parser.print_help()


# Script start Here
if __name__ == "__main__":
    main()
