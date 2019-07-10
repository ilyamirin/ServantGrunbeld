class AzureCredentials:
	SUBSCRIPTION_KEY = "d7d1ad91f1fb4f54b9bda4345c2c0614"
	SERVICE_REGION = "francecentral"


class AzureConfig:
	RESPONSE_DETAILED = "detailed"
	RESPONSE_SIMPLE = "simple"

	LANG_RUS = "ru-RU"

	REST_PATH = "speech/recognition/conversation/cognitiveservices/v1"
	REST_BASE_URL = "https://{}.stt.speech.microsoft.com".format(AzureCredentials.SERVICE_REGION)


class KaldiConfig:
	import math
	# Scaling factor for acoustic log-likelihoods (float, default = 0.1)
	# --acoustic-scale
	acoustic_scale = 0.1

	# Append pitch features to raw MFCC/PLP/filterbank features [but not for iVector extraction] (bool, default = False)
	# --add-pitch
	add_pitch = "false"

	# Decoding beam.  Larger->slower, more accurate. (float, default = 16)
	# --beam
	beam = 16

	# Increment used in decoding-- this parameter is obscure and relates to a speedup in
	# the way the max-active constraint is applied.  Larger is more accurate. (float, default = 0.5)
	# --beam-delta
	beam_delta = 0.5

	# Length of chunk size in seconds, that we process. (float, default = 0.18)
	# --chunk-length
	chunk_length_sec = 0.18

	# If True, turn on debug for the neural net computation (very verbose!)
	# Will be turned on regardless if --verbose >= 5 (bool, default = False)
	# --computation.debug
	computation_debug = "false"

	# If True, turn on debug for the actual computation (very verbose!) (bool, default = False)
	# --debug-computation
	debug_computation = "false"

	# Tolerance used in determinization (float, default = 0.000976562)
	# --delta
	delta = 0.000976562

	# If True, determinize the lattice (lattice-determinization, keeping only
	# best pdf-sequence for each word-sequence). (bool, default = True)
	# --determinize-lattice
	determinize_lattice = "true"

	# This endpointing rule requires relative-cost of final-states to be <= this
	# value (describes how good the probability of final-states is). (float, default = inf)
	# --endpoint.rule1.max-relative-cost
	endpoint_rule1_max_relative_cost = math.inf

	# This endpointing rule requires duration of trailing silence(in seconds) to be >= this value. (float, default = 5)
	# --endpoint.rule1.min-trailing-silence
	endpoint_rule1_min_trailing_silence = 5

	# This endpointing rule requires utterance-length (in seconds) to be >= this value. (float, default = 0)
	# --endpoint.rule1.min-utterance-length
	endpoint_rule1_min_utterance_length = 0

	# If True, for this endpointing rule to apply there mustbe nonsilence in the
	# best-path traceback. (bool, default = False)
	# --endpoint.rule1.must-contain-nonsilence
	endpoint_rule1_must_contain_nonsilence = "false"

	# This endpointing rule requires relative-cost of final-states to be <= this
	# value (describes how good the probability of final-states is). (float, default = 2)
	# --endpoint.rule2.max-relative-cost
	endpoint_rule2_max_relative_cost = 2

	# This endpointing rule requires duration of trailing silence(in seconds) to be >= this value. (float, default = 0.5)
	# --endpoint.rule2.min-trailing-silence
	endpoint_rule2_min_trailing_silence = 0.5

	# This endpointing rule requires utterance-length (in seconds) to be >= this value. (float, default = 0)
	# --endpoint.rule2.min-utterance-length
	endpoint_rule2_min_utterance_length = 0

	# If True, for this endpointing rule to apply there mustbe nonsilence in the
	# best-path traceback. (bool, default = True)
	# --endpoint.rule2.must-contain-nonsilence
	endpoint_rule2_must_contain_nonsilence = "true"

	# This endpointing rule requires relative-cost of final-states to be <= this
	# value (describes how good the probability of final-states is). (float, default = 8)
	# --endpoint.rule3.max-relative-cost
	endpoint_rule3_max_relative_cost = 8

	# This endpointing rule requires duration of trailing silence(in seconds) to be >= this value. (float, default = 1)
	# --endpoint.rule3.min-trailing-silence
	endpoint_rule3_min_trailing_silence = 1

	# This endpointing rule requires utterance-length (in seconds) to be >= this value. (float, default = 0)
	# --endpoint.rule3.min-utterance-length
	endpoint_rule3_min_utterance_length = 0

	# If True, for this endpointing rule to apply there mustbe nonsilence in the
	# best-path traceback. (bool, default = True)
	# --endpoint.rule3.must-contain-nonsilence
	endpoint_rule3_must_contain_nonsilence = "true"

	# This endpointing rule requires relative-cost of final-states to be <= this
	# value (describes how good the probability of final-states is). (float, default = inf)
	# --endpoint.rule4.max-relative-cost
	endpoint_rule4_max_relative_cost = math.inf

	# This endpointing rule requires duration of trailing silence(in seconds) to be >= this value. (float, default = 2)
	# --endpoint.rule4.min-trailing-silence
	endpoint_rule4_min_trailing_silence = 2

	# This endpointing rule requires utterance-length (in seconds) to be >= this value. (float, default = 0)
	# --endpoint.rule4.min-utterance-length
	endpoint_rule4_min_utterance_length = 0

	# If True, for this endpointing rule to apply there mustbe nonsilence in the
	# best-path traceback. (bool, default = True)
	# --endpoint.rule4.must-contain-nonsilence
	endpoint_rule4_must_contain_nonsilence = "true"

	# This endpointing rule requires relative-cost of final-states to be <= this
	# value (describes how good the probability of final-states is). (float, default = inf)
	# --endpoint.rule5.max-relative-cost
	endpoint_rule5_max_relative_cost = math.inf

	# This endpointing rule requires duration of trailing silence(in seconds) to be >= this value. (float, default = 0)
	# --endpoint.rule5.min-trailing-silence
	endpoint_rule5_min_trailing_silence = 0

	# This endpointing rule requires utterance-length (in seconds) to be >= this value. (float, default = 20)
	# --endpoint.rule5.min-utterance-length
	endpoint_rule5_min_utterance_length = 20

	# If True, for this endpointing rule to apply there mustbe nonsilence in the
	# best-path traceback. (bool, default = False)
	# --endpoint.rule5.must-contain-nonsilence
	endpoint_rule5_must_contain_nonsilence = "false"

	# List of phones that are considered to be silence phones by the endpointing code. (string, default = "")
	# --endpoint.silence-phones
	endpoint_silence_phones = ""

	# Extra left context to use at the first frame of an utterance (note this will
	# just consist of repeats of the first frame, and should not usually be necessary. (int, default = 0)
	# --extra-left-context-initial
	extra_left_context_initial = 0

	# Configuration file for filterbank features (e.g. conf/fbank.conf) (string, default = "")
	# --fbank-config
	fbank_config = ""

	# Base feature type [mfcc, plp, fbank] (string, default = "mfcc")
	# --feature-type
	feature_type = "mfcc"

	# Required if the frame-rate of the output (e.g. in 'chain' models) is less than
	# the frame-rate of the original alignment. (int, default = 1)
	# --frame-subsampling-factor
	frame_subsampling_factor = 1

	# Number of frames in each chunk that is separately evaluated by the neural net.
	# Measured before any subsampling, if the --frame-subsampling-factor options is
	# used (i.e. counts input frames.  This is only advisory (may be rounded up if needed. (int, default = 20)
	# --frames-per-chunk
	frames_per_chunk = 20

	# Setting used in decoder to control hash behavior (float, default = 2)
	# --hash-ratio
	hash_ratio = 2

	host = "127.0.0.1"

	# Configuration file for online iVector extraction, see class
	# OnlineIvectorExtractionConfig in the code (string, default = "")
	# --ivector-extraction-config
	ivector_extraction_config = ""

	# (RE weighting in iVector estimation for online decoding) Maximum allowed
	# duration of a single transition-id; runs with durations longer than this will
	# be weighted down to the silence-weight. (float, default = -1)
	# --ivector-silence-weighting.max-state-duration
	ivector_silence_weighting_max_state_duration = -1

	# (RE weighting in iVector estimation for online decoding) List of integer ids of
	# silence phones, separated by colons (or commas).  Data that (according to the
	# traceback of the decoder) corresponds to these phones will be downweighted
	# by --silence-weight. (string, default = "")
	# --ivector-silence-weighting.silence-phones
	ivector_silence_weighting_silence_phones = ""

	# (RE weighting in iVector estimation for online decoding) Weighting factor for
	# frames that the decoder trace-back identifies as silence; only relevant if
	# the --silence-phones option is set. (float, default = 1)
	# --ivector-silence-weighting.silence-weight
	ivector_silence_weighting_silence_weight = 1

	# Lattice generation beam.  Larger->slower, and deeper lattices (float, default = 10)
	# --lattice-beam
	lattice_beam = 10

	# Decoder max active states.  Larger->slower; more accurate (int, default = 2147483647)
	# --max-active
	max_active = 2147483647

	# Maximum approximate memory usage in determinization (real usage might be many times this). (int, default = 50000000)
	# --max-mem
	max_mem = 50000000

	# Configuration file for MFCC features (e.g. conf/mfcc.conf) (string, default = "")
	# --mfcc-config
	mfcc_config = ""

	# Decoder minimum active states. (int, default = 200)
	# --min-active
	min_active = 200

	# If True, push and minimize after determinization. (bool, default = False)
	# --minimize
	minimize = "false"

	# Number of threads used when initializing iVector extractor. (int, default = 8)
	# --num-threads-startup
	num_threads_startup = 8

	# Configuration file for online pitch features, if --add-pitch=true
	# (e.g. conf/online_pitch.conf) (string, default = "")
	# --online-pitch-config
	online_pitch_config = ""

	# Instead of deleting a matrix of a given size and then allocating a matrix
	# of the same size, allow re-use of that memory (bool, default = True)
	# --optimization.allocate-from-other
	optimization_allocate_from_other = "true"

	# Set to False to disable left-merging of variables in remove-assignments (obscure option) (bool, default = True)
	# --optimization.allow-left-merge
	optimization_allow_left_merge = "true"

	# Set to False to disable right-merging of variables in remove-assignments (obscure option) (bool, default = True)
	# --optimization.allow-right-merge
	optimization_allow_right_merge = "true"

	# Set to False to disable optimization that allows in-place backprop (bool, default = True)
	# --optimization.backprop-in-place
	optimization_backprop_in_place = "true"

	# Set to False to disable optimization that consolidates the model-update
	# phase of backprop (e.g. for recurrent architectures (bool, default = True)
	# --optimization.consolidate-model-update
	optimization_consolidate_model_update = "true"

	# Set to False to disable the optimization that converts Add commands into
	# Copy commands wherever possible. (bool, default = True)
	# --optimization.convert-addition
	optimization_convert_addition = "true"

	# This optimization can reduce memory requirements for TDNNs when applied
	# together with --convert-addition=True (bool, default = True)
	# --optimization.extend-matrices
	optimization_extend_matrices = "true"

	# Set to False to disable optimization that avoids redundant zeroing (bool, default = True)
	# --optimization.initialize-undefined
	optimization_initialize_undefined = "true"

	# You can set this to the maximum t value that you want derivatives to be
	# computed at when updating the model.  This is an optimization that
	# saves time in the backprop phase for recurrent frameworks (int, default = 2147483647)
	# --optimization.max-deriv-time
	optimization_max_deriv_time = 2147483647

	# An alternative mechanism for setting the --max-deriv-time, suitable for
	# situations where the length of the egs is variable.  If set, it is
	# equivalent to setting the --max-deriv-time to this value plus the
	# largest 't' value in any 'output' node of the computation request. (int, default = 2147483647)
	# --optimization.max-deriv-time-relative
	optimization_max_deriv_time_relative = 2147483647

	# This is only relevant to training, not decoding.  Set this to 0,1,2; higher
	# levels are more aggressive at reducing memory by compressing quantities
	# needed for backprop, potentially at the expense of speed and the accuracy
	# of derivatives.  0 means no compression at all; 1 means compression
	# that shouldn't affect results at all. (int, default = 1)
	# --optimization.memory-compression-level
	optimization_memory_compression_level = 1

	# You can set this to the minimum t value that you want derivatives to be
	# computed at when updating the model.  This is an optimization that saves
	# time in the backprop phase for recurrent frameworks (int, default = -2147483648)
	# --optimization.min-deriv-time
	optimization_min_deriv_time = -2147483648

	# Set to False to disable optimization that moves matrix allocation and
	# deallocation commands to conserve memory. (bool, default = True)
	# --optimization.move-sizing-commands
	optimization_move_sizing_commands = "true"

	# Set this to False to turn off all optimizations (bool, default = True)
	# --optimization.optimize
	optimization_optimize = "true"

	# Set to False to disable certain optimizations that act on operations of type *Row*. (bool, default = True)
	# --optimization.optimize-row-ops
	optimization_optimize_row_ops = "true"

	# Set to False to disable optimization that allows in-place propagation (bool, default = True)
	# --optimization.propagate-in-place
	optimization_propagate_in_place = "true"

	# Set to False to disable optimization that removes redundant assignments (bool, default = True)
	# --optimization.remove-assignments
	optimization_remove_assignments = "true"

	# Set this to False to disable an optimization that reduces the size of
	# certain per-row operations (bool, default = True)
	# --optimization.snip-row-ops
	optimization_snip_row_ops = "true"

	# Set to False to disable an optimization that may replace some operations
	# of type kCopyRowsMulti or kAddRowsMulti with up to two simpler operations. (bool, default = True)
	# --optimization.split-row-ops
	optimization_split_row_ops = "true"

	# How often in seconds, do we check for changes in output. (float, default = 1)
	# --output-period
	output_period = 1

	# If True, do an initial pass of determinization on both phones and words
	# (see also --word-determinize) (bool, default = True)
	# --phone-determinize
	phone_determinize = "true"

	# Configuration file for PLP features (e.g. conf/plp.conf) (string, default = "")
	# --plp-config
	plp_config = ""

	# Port number the server will listen on. (int, default = 5050)
	# --port-num
	port = 5063

	# Interval (in frames) at which to prune tokens (int, default = 25)
	# --prune-interval
	prune_interval = 25

	# Number of seconds of timout for TCP audio data to appear on the stream. Use -1 for blocking. (int, default = 3)
	# --read-timeout
	read_timeout = 3

	# Sampling frequency of the input signal (coded as 16-bit slinear). (float, default = 16000)
	# --samp-freq
	samp_freq = 16000

	# If True, do a second pass of determinization on words only (see also --phone-determinize) (bool, default = True)
	# --word-determinize
	word_determinize = "true"

	chunk_length = int(samp_freq * chunk_length_sec)
