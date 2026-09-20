"""Offline conversion: verified sat-water ResNet34 U-Net to CPU ONNX inference."""
import os
os.environ['TF_USE_LEGACY_KERAS']='1'
os.environ['SM_FRAMEWORK']='tf.keras'
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
from pathlib import Path
import hashlib,json
import numpy as np
import tensorflow as tf
import segmentation_models as sm
import tf2onnx
ROOT=Path(__file__).resolve().parents[1]

def main():
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    folder=ROOT/'models/checkpoints/rgb_water_unet'
    manifest=json.loads((folder/'source_manifest.json').read_text())
    expected=manifest['models']['resnet34_256']['sha256']
    assert hashlib.sha256((folder/'weights.h5').read_bytes()).hexdigest()==expected
    model=sm.Unet('resnet34',classes=2,activation='softmax',encoder_weights=None,input_shape=(256,256,3))
    model.load_weights(str(folder/'weights.h5'))
    # The backbone preprocessing is identity; sat-water subsequently performs a
    # common (not per-channel) min/max normalization on each RGB patch.
    sample=np.random.default_rng(41).random((1,256,256,3)).astype('float32')
    assert np.allclose(sm.get_preprocessing('resnet34')(sample.copy()),sample)
    signature=(tf.TensorSpec((None,256,256,3),tf.float32,name='rgb'),)
    @tf.function(input_signature=signature)
    def forward(rgb):return model(rgb,training=False)
    tf2onnx.convert.from_function(forward,input_signature=signature,opset=15,output_path=str(folder/'model.onnx'))
    np.savez(folder/'conversion_reference.npz',input=sample,output=model(sample,training=False).numpy())
    (folder/'conversion.json').write_text(json.dumps({'source_sha256':expected,'onnx_sha256':hashlib.sha256((folder/'model.onnx').read_bytes()).hexdigest(),
        'source':'https://huggingface.co/busayojee/sat-water-weights','revision':'1beb2b798eb8616eeba1e52aa1c22986f8fbfbcb',
        'water_channel':1,'preprocessing':'Common patch min/max across RGB; no per-channel stretch','opset':15},indent=2))
    print('Converted',flush=True)
if __name__=='__main__':main()
