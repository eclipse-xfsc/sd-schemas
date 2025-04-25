mkdir -p widoco/
touch widoco/index.html
mkdir -p widoco/provider/
cp implementation/instances/provider/*.ttl widoco/provider/ 2>/dev/null || true
cp implementation/instances/provider/*.jsonld widoco/provider/ 2>/dev/null || true
mkdir -p widoco/constraints/
cp implementation/instances/service-offering/*.ttl widoco/service/ 2>/dev/null || true
cp implementation/instances/service-offering/*.jsonld widoco/service/ 2>/dev/null || true
cd widoco && find . -name \*.ttl -o -name \*.jsonld > files.txt
cd ..
echo "TTL and JSON-LD file provisioning done. Starting documentation..."
apt-get update
apt-get -y install default-jdk
echo "Creating documentation..."
wget https://github.com/dgarijo/Widoco/releases/download/v1.4.15_1/widoco-1.4.15-jar-with-dependencies.jar -O widoco.jar

for filename in yaml2ontology/*.ttl; do
  name_generated=$(basename "$filename" .ttl)
  name=${name_generated%_*}
  mkdir -p widoco/$name/
  echo "Creating $name documentation..."
  java -jar widoco.jar -ontFile $filename -outFolder doc_$name -webVowl -uniteSections -rewriteAll
  sed -i '/<tr><td><b>gax-$name<\/b><\/td><td>&lt;http:\/\/w3id.org\/gaia-x\/$name#&gt;<\/td><\/tr>/d' doc_$name/index-en.html
  mv doc_$name/index-en.html doc_$name/$name.html
  cp -r doc_$name/* widoco/$name/
  rm widoco/$name/webvowl/data/ontology.json
  java -jar ./toolchain/owl2vowl.jar -file widoco/$name/ontology.xml
  mv ontology.json widoco/$name/webvowl/data/
done

echo "Create JSONLD Visualization"
mkdir -p widoco/visualization/
cp -r toolchain/visualization/* widoco/visualization/
mv toolchain/constraints.html widoco/
mkdir -p widoco/validation/
cp -r yaml2shacl/* widoco/validation
#mkdir -p widoco/json-validation/
#cp -r yaml2json/* widoco/json-validation/
mkdir -p widoco/ontology_autogen/
cp -r yaml2ontology/* widoco/ontology_autogen/