# we'll use this to open script files

class FileMgr:

    # def __init__(self):

    def ParseScriptFile(self, thefilename):
        script = []
        self.filename = thefilename
        with open(self.filename, 'r') as f:
            for line in f:
                index = line.find('#')  # the # is a comment line
                if index > -1:
                    line = line[:index].strip()

                if len(line.strip()) > 1:  # skip blank lines
                    script.append(line.strip())

        return script
