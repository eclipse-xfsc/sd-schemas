location='../../implementation/instances'
outputLocation='output'

npm i
mkdir $outputLocation
cp -R $location $outputLocation

while IFS= read -r -d '' file
do
  filename_with_extension="$(basename -- "$file")"
  filename="${filename_with_extension%.jsonld}"
  directory=${file%/*}
  subdirectory="${directory}/${filename}"
  mkdir "$subdirectory"
  cp index.html "$subdirectory"
  cp index.css "$subdirectory"
  mv "$file" "$subdirectory"
  node ./node_modules/browserify/bin/cmd.js index.js -t [ envify --FILE "$filename_with_extension" ] -o "${subdirectory}/bundle.js"
done <   <(find $outputLocation -type f -name "*.jsonld" -print0)
