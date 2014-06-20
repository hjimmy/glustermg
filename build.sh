name="glustermg"
version="2.4"
structure="x86_64"
fullname=$name-$version.$structure
cp -rf  source $fullname
tar -zcvf $fullname.tar.gz $fullname
cp -rf $fullname.tar.gz   ~/rpmbuild/SOURCES
cp -rf *.spec ~/rpmbuild/SPECS
rpmbuild -bs --nodeps ~/rpmbuild/SPECS/$name.spec
