
import os
import sys

#basedir ='public/'

html = \
'<html>\n' \
'<head>\n' \
'    <meta http-equiv="refresh" content="0; URL=' + os.getenv("CI_COMMIT_REF_NAME") + '/index.html" />\n' \
'</head>\n' \
'<body>\n' \
'    <p>If you are not redirected, <a href="' + os.getenv("CI_COMMIT_REF_NAME") + '/index.html">click here</a></p>\n' \
'</body>\n' \
'</html>'


if __name__ == '__main__':

    basedir = sys.argv[1] + "/"

    # Write the new structure to the same HTML file
    with open(os.path.join(basedir, "index.html"), "w") as outf:
        outf.write(str(html))
