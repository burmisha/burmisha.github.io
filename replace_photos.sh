#!/usr/bin/env bash
set -xue -o posix -o pipefail

old=old_links.lst
new=new_links.lst
file=_posts/2014-09-20-yachtit.html

N=$(wc -l $old | awk '{print $1}')
i=1
cp $file $file.1
while [[ i -le $N ]]; do
	o=$(awk 'NR=='$i $old)
	n=$(awk 'NR=='$i $new)
	cat $file.1 | sed 's|'$o'|'$n'|g' >$file.2
	mv $file.2 $file.1
	i=$((i+1))
done
