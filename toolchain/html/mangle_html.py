import os
import bs4
import sys

# basedir = 'public/'
widoco = "widoco"

if __name__ == '__main__':

    basedir = sys.argv[1] + "/"

    for version_dirs in os.walk(basedir):
        for vdir in sorted(version_dirs[1]):
            if vdir == widoco:
                # exclude widoco folder
                continue

            if os.path.isfile(os.path.join(basedir + vdir, "index.html")):
                html = ""
                # Load the HTML file
                with open(basedir + vdir + "/index.html") as inf:
                    txt = inf.read()
                    html = bs4.BeautifulSoup(txt, features="html.parser")

                for vp in html.find_all("div", {'id': 'wy-version-pick'}):
                    vp.decompose()

                # Create the dropdown tag
                dropdown = html.new_tag("div", style="padding: .809em;")
                dropdown['class'] = "wy-version-pick"
                # Insert it at the specified location
                navs = html.find_all("div", {"class": "wy-side-nav-search"})
                navs[0].insert_after(dropdown)

                # Find the previously added div
                divs = html.find_all("div", {"class": "wy-version-pick"})

                # Create the select tag
                select = html.new_tag("select",
                                      style="width: 70%; border-radius: 50px; padding: 6px 12px; border-color: #2472a4; margin-left: 12%;")
                select['id'] = "version-picker"
                select['name'] = "version-picker"
                select['onChange'] = "window.location.href=this.value"

                # Create all option tags
                for dirs in os.walk(basedir):
                    for dir in sorted(dirs[1]):  # << this isnt good i guess
                        if dir == widoco:
                            continue
                        if os.path.isfile(os.path.join(basedir + dir, "index.html")):
                            option = html.new_tag("option", value="../" + dir + "/index.html")
                            option.append("Version " + dir)
                            if dir == vdir:
                                option["selected"] = "true"
                            select.append(option)

                # Append the select tag
                divs[0].append(select)

                # Write the new structure to the same HTML file
                with open(basedir + vdir + "/index.html", "w") as outf:
                    outf.write(str(html))

    print("HTMLs mangled...")
