import subprocess
import string
import sys
import os
import errno
import re
import shutil

ITER_BEGIN = re.compile('\s*@iter\s+(.+?)@\s*')
ITER_END   = re.compile('\s*@end@\s*')

ARDUINO_PATH = '/Applications/Arduino.app/Contents/Java/hardware/tools/avr/bin'


def exec_iter(items, template, output):
    lines = []
    for line in template:
        m = ITER_END.match(line)
        if m:
            break
        else:
            lines.append(line)

    for item in items:
        for line in lines:
            output.write(line.format(**item))


def exec_template(from_template, to, model):
    with open(from_template, 'r') as template:
        with open(to, 'w') as output:
            for line in template:
                m = ITER_BEGIN.match(line)
                if m:
                    list = model[m.group(1)]
                    exec_iter(list, template, output)
                else:
                    output.write(line.format(**model))


def mcu_to_def(mcu):
    defi = mcu.upper()
    families = ['XMEGA', 'MEGA', 'TINY']
    for family in families:
        defi = defi.replace(family, family.lower())
    return '__AVR_' + defi + '__'


def supported_mcus():
    HEADER = 'Known MCU names:'

    proc = subprocess.Popen('avr-gcc -Wa,-mlist-devices --target-help', stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=True)
    out, err = proc.communicate()
    exitcode = proc.returncode
    lines = string.split(out, '\n')

    mcus = []
    consider = False
    for line in lines:
        if HEADER in line:
            consider = True
        elif consider:
            if line.startswith(' '):
                for mcu in line.split():
                    mcus.append({'mcu': mcu, 'defi': mcu_to_def(mcu)})
            else:
                break

    return mcus


def supported_programmers():
    HEADER = 'Valid programmers are:'
    PROG_LINE = re.compile('  (.+?)\s+=.*')

    proc = subprocess.Popen('avrdude -c?', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    exitcode = proc.returncode
    lines = string.split(err, '\n')

    programmers = []
    consider = False
    for line in lines:
        if line == HEADER:
            consider = True
        elif consider:
            m = PROG_LINE.match(line)
            if m:
                programmers.append({'programmer': m.group(1)})
            else:
                break

    return programmers


def avr_loc():
    bin_path = subprocess.check_output('which avr-gcc', shell=True).strip()
    return os.path.dirname(os.path.dirname(os.path.realpath(bin_path)))


def avrdude_loc():
    return subprocess.check_output('which avrdude', shell=True).strip()


def parse_system_includes(toolpaths):
    """
    Parses the output of "avr-cpp -v" command to find the system include paths.

    :return: list of include directories checked when #include <...> is seen by preprocessor.
    """
    command = 'echo | {cpp} -v'.format(cpp=toolpaths['avr-cpp_loc'])
    ISYS    = '#include <...> search starts here:'

    print
    print "Parsing avr-cpp system include paths.";
    print 'Checking output of "{0}"'.format(command)

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    # exitcode = proc.returncode

    lines = string.split(err, '\n')
    system_includes = []

    consider = False
    for line in lines:
        if line == ISYS:
            consider = True
        elif consider:
            if line.startswith(' '):
                system_includes.append(os.path.normpath(line.strip()))
            else:
                break

    for s in system_includes:
        print 'Found system include: {0}'.format(s)

    return system_includes


def ensure_installed(tool):
    """
    Tries to find :param tool: on the PATH, or, checks to see if Arduino.app was installed
    and tries to find :param tool: somewhere in there.

    :returns: path to the tool executable, or None if not found
    """
    proc = subprocess.Popen('which ' + tool, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    exitcode = proc.returncode

    if exitcode == 0:
        print('Found {t:<11} install in "{p}"'.format(t=tool, p=out.strip()))
        return out.strip()
    else:
        print('{t:<11} is not installed (or is not in the PATH).'.format(t=tool))
        return None


def ensure_installed_arduino(tool):
    tool_path = os.path.join(ARDUINO_PATH, tool)
    if os.path.isfile(tool_path):
        print('Found {t:<11} install in "{p}"'.format(t=tool, p=tool_path))
        return tool_path
    else:
        print('{t:<11} is not installed (or is not in the PATH).'.format(t=tool))
        return None


def mkdirs_p(dirs):
    try:
        os.makedirs(dirs)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise


def main():
    toolpaths = {}
    tools     = ['avr-cpp', 'avr-gcc', 'avr-objcopy', 'avr-objdump', 'avr-size', 'avr-nm', 'avrdude']

    # Find the tools on the PATH.
    print
    print "Searching for AVR tools in the PATH folders ({path})".format(path=os.environ['PATH'])
    for tool in tools:
        toolpaths[tool + '_loc'] = ensure_installed(tool)

    # If any tools are missing, consider that an error.
    # Try finding them in Arduino.app.
    if None in toolpaths.values():
        print "Could not find all tools in the PATH folders."
        print
        print "Searching {ap}".format(ap=ARDUINO_PATH)
        for tool in tools:
            toolpaths[tool + '_loc'] = ensure_installed_arduino(tool)

    # Check again, if any tools are missing, then exit.
    if None in toolpaths.values():
        print "Could not find all tools in the Arduino.app package."
        print "Exiting."
        exit(1)

    exec_template('Makefile.tpl', 'Makefile', toolpaths)

    model = {'isystem': ' '.join(parse_system_includes(toolpaths)),
             'mcus': supported_mcus(),
             'programmers': supported_programmers()
             }
    print model

    return

    exec_template('TemplateInfo.plist.tpl', 'TemplateInfo.plist', model)

    print('Generated template:\n\tMCUs        : {}\n\tProgrammers : {}'
          .format(len(model['mcus']), len(model['programmers'])))

    DEST_DIR = os.path.join(os.path.expanduser('~'),
                            'Library/Developer/Xcode/Templates/Project Template/xavr/xavr.xctemplate/')
    print('Installing template in: "{}"'.format(DEST_DIR))
    mkdirs_p(DEST_DIR)
    shutil.copy('main.c', DEST_DIR)
    shutil.copy('Makefile', DEST_DIR)
    shutil.copy('TemplateInfo.plist', DEST_DIR)
    shutil.copy('TemplateIcon.icns', DEST_DIR)

    os.remove('Makefile')
    os.remove('TemplateInfo.plist')
    print('Done. Hack away !\n')


if __name__ == '__main__':
    main()
