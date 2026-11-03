#!/bin/bash
# 成績(K)・番組表(B)のサンプルを展開してUTF-8で保存する(形式確認用)
set -e
mkdir -p tmp sample
for d in 20261101 20240115; do
  ym=${d:0:6}; yymmdd=${d:2:6}
  for k in K B; do
    kl=$(echo $k | tr A-Z a-z)
    curl -sSf -A "Mozilla/5.0" -o tmp/$k$d.lzh "https://www1.mbrace.or.jp/od2/$k/$ym/$kl$yymmdd.lzh"
    (cd tmp && lha xq $k$d.lzh)
  done
done
for f in tmp/*.txt tmp/*.TXT; do [ -f "$f" ] && iconv -f CP932 -t UTF-8 "$f" > sample/$(basename "$f").utf8.txt || true; done
ls -la sample
