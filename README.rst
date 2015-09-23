Scripts for benchmarking gcc

perf.py: taken from revision b868d0a9c5d7 of http://hg.python.org/benchmarks
which is under an MIT-style license.
with an edit to ShortenUrl(url) to replace "return None" with "return url"

test-sources/big-code.c:
  Several large functions  with arithmetics and one-deep loops, posted by
  Michael Matz to gcc-patches:
    https://gcc.gnu.org/ml/gcc-patches/2013-09/msg00062.html

test-sources/empty.c:
  Empty file

test-sources/kdecore.cc:
  Preprocessed real world C++ library code from 2009, posted by
  Michael Matz to gcc-patches:
    https://gcc.gnu.org/ml/gcc-patches/2013-09/msg00062.html
