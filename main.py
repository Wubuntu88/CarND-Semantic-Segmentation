#!/usr/bin/env python3
import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests

# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights
    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'

    tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)

    graph = tf.get_default_graph()
    w1 = graph.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob = graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    layer3 = graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    layer4 = graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    layer7 = graph.get_tensor_by_name(vgg_layer7_out_tensor_name)
    
    return w1, keep_prob, layer3, layer4, layer7
tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer3_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer7_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function
    conv_1x1_layer_7 = tf.layers.conv2d(inputs=vgg_layer7_out,
                                        filters=num_classes,
                                        kernel_size=1,
                                        padding="SAME",
                                        kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                        kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                                        name="conv_1x1_layer_7")
    conv_1x1_layer_4 = tf.layers.conv2d(inputs=vgg_layer4_out,
                                        filters=num_classes,
                                        kernel_size=1,
                                        padding="SAME",
                                        kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                        kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                                        name="conv_1x1_layer_4")
    conv_1x1_layer_3 = tf.layers.conv2d(inputs=vgg_layer3_out,
                                        filters=num_classes,
                                        kernel_size=1,
                                        padding="SAME",
                                        kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                        kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                                        name="conv_1x1_layer_3")

    layer_7_deconv = tf.layers.conv2d_transpose(inputs=conv_1x1_layer_7,
                                                filters=num_classes,
                                                kernel_size=4,
                                                strides=2,
                                                padding="SAME",
                                                kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                                kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                                                name="decoder_layer_1")

    skip_4_and_7 = tf.add(layer_7_deconv, conv_1x1_layer_4)

    skip_4_and_7_deconv = tf.layers.conv2d_transpose(inputs=skip_4_and_7,
                                                     filters=num_classes,
                                                     kernel_size=4,
                                                     strides=2,
                                                     padding="SAME",
                                                     kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                                     kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                                                     name="decoder_layer_2")

    skip_3_4_and_7 = tf.add(skip_4_and_7_deconv, conv_1x1_layer_3)

    skip_3_4_and_7_deconv = tf.layers.conv2d_transpose(inputs=skip_3_4_and_7,
                                                       filters=num_classes,
                                                       kernel_size=16,
                                                       strides=8,
                                                       padding="SAME",
                                                       kernel_initializer=tf.truncated_normal_initializer(stddev=0.01),
                                                       kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                                                       name="decoder_layer_3")
    return skip_3_4_and_7_deconv
tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    logits = tf.reshape(nn_last_layer, (-1, num_classes))

    softmax_cross_entropy_loss = tf.nn.softmax_cross_entropy_with_logits(logits=logits,
                                                                         labels=correct_label)
    loss_operaton = tf.reduce_mean(softmax_cross_entropy_loss)

    adam_optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)

    training_operation = adam_optimizer.minimize(loss=loss_operaton)

    return logits, training_operation, loss_operaton
tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    batch_no = 0
    for epoch in range(epochs):
        for image, label in get_batches_fn(batch_size):
            _, loss = sess.run([train_op, cross_entropy_loss],
                               feed_dict={input_image: image, correct_label: label,
                                          keep_prob: 0.5, learning_rate: 0.001})
            print("Epoch: {}, Batch #: {}, loss: {}".format(epoch, batch_no, loss))
            batch_no += 1
tests.test_train_nn(train_nn)


def run():
    num_classes = 2
    image_shape = (160, 576)  # KITTI dataset uses 160x576 images
    data_dir = './data'
    runs_dir = './runs'
    tests.test_for_kitti_dataset(data_dir)

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/
    print("starting session")
    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network
        print("creating layer output")
        # TODO: Build NN using load_vgg, layers, and optimize function
        input_image, keep_prob, layer_3_out, layer_4_out, layer_7_out = load_vgg(sess=sess, vgg_path=vgg_path)
        layer_output = layers(vgg_layer3_out=layer_3_out,
                              vgg_layer4_out=layer_4_out,
                              vgg_layer7_out=layer_7_out,
                              num_classes=num_classes)

        correct_label = tf.placeholder(tf.float32, [None, None, None, num_classes], name='correct_label')
        learning_rate = tf.placeholder(tf.float32, name='learning_rate')

        logits, train_op, cross_entropy_loss = optimize(nn_last_layer=layer_output,
                                                        correct_label=correct_label,
                                                        learning_rate=learning_rate,
                                                        num_classes=num_classes)

        print("training model")
        # TODO: Train NN using the train_nn function
        epochs = 25
        batch_size = 5
        sess.run(tf.global_variables_initializer())
        train_nn(sess=sess,
                 epochs=epochs,
                 batch_size=batch_size,
                 get_batches_fn=get_batches_fn,
                 train_op=train_op,
                 cross_entropy_loss=cross_entropy_loss,
                 input_image=input_image,
                 correct_label=correct_label,
                 keep_prob=keep_prob,
                 learning_rate=learning_rate)

        print("saving inference")
        # TODO: Save inference data using helper.save_inference_samples
        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        # OPTIONAL: Apply the trained model to a video


if __name__ == '__main__':
    run()
