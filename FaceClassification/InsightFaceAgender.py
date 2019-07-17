import numpy as np
import mxnet as mx


class AgenderClassifier:
	def __init__(self, prefix, epoch, ctxID=0):
		self.net = self._initEmbedder(prefix, epoch, ctxID)


	def _initEmbedder(self, prefix, epoch, ctx, shape=(112, 112), layer="fc1"):
		if ctx >= 0:
			ctx = mx.gpu(ctx)
		else:
			ctx = mx.cpu()

		sym, arg_params, aux_params = mx.model.load_checkpoint(prefix, epoch)
		all_layers = sym.get_internals()
		sym = all_layers[layer + '_output']

		model = mx.mod.Module(symbol=sym, context=ctx, label_names=None)

		model.bind(data_shapes=[('data', (1, 3) + shape)])
		model.set_params(arg_params, aux_params)

		return model


	def getFaceAgender(self, face):
		input_blob = np.expand_dims(face, axis=0)

		data = mx.nd.array(input_blob)
		db = mx.io.DataBatch(data=(data,))
		self.net.forward(db, is_train=False)

		ret = self.net.get_outputs()[0].asnumpy()

		g = ret[:, 0:2].flatten()
		gender = np.argmax(g)

		a = ret[:, 2:202].reshape((100, 2))
		a = np.argmax(a, axis=1)
		age = int(sum(a))

		return age, gender
