import glob

def createIndex():
    index = open('../yaml2shacl/index.html', 'w')
    index.write('<!DOCTYPE html>\n<html>\n<head>\n\t<title>SHACL Shapes</title>\n</head>\n<body>\n\n<table border="2" cellspacing="0" cellpadding="10">\n')

    index.write('\t<tr>\n')
    index.write('\t\t<th>SHACL Shape</th>\n')
    index.write('\t\t<th>UML Visualization</th>\n')
    index.write('\t</tr>\n')

    for filename in glob.glob('../yaml2shacl/*.ttl'):
        filename = filename.split('/')[2].split('.')[0]
        index.write('\t<tr>\n')
        index.write('\t\t<td><a href="https://gaia-x.gitlab.io/technical-committee/service-characteristics/yaml2shacl/%s.ttl">%s.ttl</a></td>\n' % (filename,filename))
        index.write('\t\t<td><img src="../shacl2uml/%s.png" alt="%s.png"></td>\n' % (filename,filename))
        index.write('\t</tr>\n')

    index.write('\n</table>\n\n</body>\n</html>')



if __name__ == "__main__":
    createIndex()