#!/bin/bash

export KALDI_ROOT=$HOME/projects/kaldi
export CONFIG_ROOT=$HOME/projects/kaldi-ru-0.6

export PATH=$PWD/utils:$KALDI_ROOT/src/bin:$KALDI_ROOT/tools/openfst/bin:$KALDI_ROOT/src/fstbin:$KALDI_ROOT/src/gmmbin:$KALDI_ROOT/src/featbin:$KALDI_ROOT/src/lm:$KALDI_ROOT/src/sgmmbin:$KALDI_ROOT/src/sgmm2bin:$KALDI_ROOT/src/fgmmbin:$KALDI_ROOT/src/latbin:$KALDI_ROOT/src/nnetbin:$KALDI_ROOT/src/nnet2bin:$KALDI_ROOT/src/online2bin:$KALDI_ROOT/src/ivectorbin:$KALDI_ROOT/src/lmbin:$KALDI_ROOT/src/chainbin:$KALDI_ROOT/src/nnet3bin:$PWD:$PATH:$KALDI_ROOT/tools/sph2pipe_v2.5
export LC_ALL=C

online2-tcp-nnet3-decode-faster \
      --frame-subsampling-factor=2 --frames-per-chunk=51 \
      --acoustic-scale=1.0 --beam=12.0 --lattice-beam=6.0 --max-active=10000 \
      --config=$CONFIG_ROOT/exp/tdnn/conf/online.conf $1 $2 $3 $4 $5 $6 $7 $8 $9\
      $CONFIG_ROOT/exp/tdnn/final.mdl $CONFIG_ROOT/exp/tdnn/graph/HCLG.fst $CONFIG_ROOT/exp/tdnn/graph/words.txt #|
    # lattice-lmrescore --lm-scale=-1.0 ark:- 'fstproject --project_output=true data/lang_test_rescore/G.fst |' ark:- |
    # lattice-lmrescore-const-arpa ark:- data/lang_test_rescore/G.carpa ark:- |
    # lattice-align-words data/lang_test_rescore/phones/word_boundary.int exp/tdnn/final.mdl ark:- ark:- |
    # lattice-to-ctm-conf --frame-shift=0.03 --acoustic-scale=0.08333 ark:- - |
    # local/int2sym.pl -f 5 data/lang_test_rescore/words.txt - -



# nnet3-in: exp/tdnn/final.mdl
# fst-in: exp/tdnn/graph/HCLG.fst
# spk2utt-rspecifier: ark:test.utt2spk
# wav-rspecifier: scp:test.scp
# lattice-wspecifier: ark:- 
# word-symbol-table: exp/tdnn/graph/words.txt
# --port-num: Port number the server will listen on. (int, default = 5050)
