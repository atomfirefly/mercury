from mwr.droidhg.modules import common, Module
from mwr.droidhg.reflection import ReflectionException

class Traversal(Module, common.ClassLoader, common.FileSystem, common.PackageManager, common.Provider, common.Strings, common.ZipFile):

    name = "Test content providers for basic directory traversal vulnerabilities."
    description = "Finds content providers with basic directory traversal vulnerabilities."
    examples = ""
    author = "Nils (@mwrlabs)"
    date = "2012-11-06"
    license = "MWR Code License"
    path = ["scanner", "provider"]

    def add_arguments(self, parser):
        parser.add_argument("package_or_uri", help="specify a package to search for content uris", metavar="package or uri", nargs="?")

    def execute(self, arguments):
        vulnerable = set([])
        uris = set([])

        if arguments.package_or_uri != None and arguments.package_or_uri.startswith("content://"):
            uris.add(arguments.package_or_uri)

            self.__test_uri(arguments.package_or_uri, vulnerable)
        else:
            for uri in self.findAllContentUris(arguments.package_or_uri):
                uris.add(uri)

                self.__test_uri(uri, vulnerable)

        # remove the collection of vulnerable URIs from the set of all URIs
        uris = uris - vulnerable

        # print out a report
        self.stdout.write("Not Vulnerable:\n")
        if len(uris) > 0:
            for uri in uris:
                self.stdout.write("  %s\n" % uri)
        else:
            self.stdout.write("  No non-vulnerable URIs found.\n")

        self.stdout.write("\nVulnerable Providers:\n")
        if len(vulnerable) > 0:
            for uri in vulnerable:
                self.stdout.write("  %s\n" % uri)
        else:
            self.stdout.write("  No vulnerable providers found.\n")

    def __test_uri(self, uri, vulnerable):
        try:
            data = self.contentResolver().read(uri + "/../../../../../../../../../../../../../../../../etc/hosts")
        except ReflectionException as e:
            if e.message.find("java.io.FileNotFoundException") >= 0 or \
                e.message.find("java.lang.IllegalArgumentException") >= 0 or \
                e.message.find("java.lang.SecurityException") >= 0 or \
                e.message.find("No content provider") >= 0 or \
                e.message.find("RuntimeException"):
                data = ""
            else:
                raise
    
        if len(data) > 0:
            vulnerable.add(uri)
            