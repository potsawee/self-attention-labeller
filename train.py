import os
import sys
import random
import tensorflow as tf
import argparse
import pdb

from labeller import Labeller
from helper import load_vocab, load_ged_data, construct_training_data_batches

def train(config):
    batches, vocab_size, word2id = construct_training_data_batches(config)
    id2word = list(word2id.keys())

    config['vocab_size'] = vocab_size

    model = Labeller(config)
    model.build_netowrk()

    if config['use_gpu']:
        if 'X_SGE_CUDA_DEVICE' in os.environ:
            print('running on the stack...')
            cuda_device = os.environ['X_SGE_CUDA_DEVICE']
            print('X_SGE_CUDA_DEVICE is set to {}'.format(cuda_device))
            os.environ['CUDA_VISIBLE_DEVICES'] = cuda_device

        else: # development only e.g. air202
            print('running locally...')
            os.environ['CUDA_VISIBLE_DEVICES'] = '3' # choose the device (GPU) here

        sess_config = tf.ConfigProto(allow_soft_placement=True)
        sess_config.gpu_options.allow_growth = True # Whether the GPU memory usage can grow dynamically.
        sess_config.gpu_options.per_process_gpu_memory_fraction = 0.95 # The fraction of GPU memory that the process can use.

    else:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        sess_config = tf.ConfigProto()

    sys.stdout.flush()

    with tf.Session(config=sess_config) as sess:
        sess.run(tf.global_variables_initializer())

        tf_variables = tf.trainable_variables()
        for i in range(len(tf_variables)):
            print(tf_variables[i])

        # pdb.set_trace()

        num_epochs = config['num_epochs']
        for epoch in range(num_epochs):
            random.shuffle(batches)

            total_loss = 0

            for i, batch in enumerate(batches):
                feed_dict = { model.word_ids: batch['word_ids'],
                            model.label_ids: batch['label_ids'],
                            model.sent_lengths: batch['sent_lengths']}

                # ------ debugging ------ #
                # logits, crossent_masked = sess.run([model.logits, model.crossent_masked], feed_dict=feed_dict)
                # pdb.set_trace()
                # ----------------------- #


                _, loss = sess.run([model.train_op, model.loss], feed_dict=feed_dict)
                total_loss += loss

            print('epoch {} --- loss = {}'.format(epoch, total_loss))

            my_sent = [word2id['<s>'], word2id['i'], word2id['wants'], word2id['to'], word2id['run'], word2id['</s>']]
            my_sent_len = len(my_sent)
            my_sent = my_sent + [word2id['</s>']] * (config['max_sentence_length'] - my_sent_len)
            feed_dict = {model.word_ids: [my_sent], model.sent_lengths: [my_sent_len]}
            probs = sess.run(model.probabilities, feed_dict=feed_dict)

            for j, word in enumerate(my_sent):
                print("{:10s} --- {:.4f}".format(id2word[word], probs[0][j][0]))
                sys.stdout.flush()
                if j == my_sent_len-1:
                    break

def main():
    # ------- config ------- #
    config = {}
    config['learning_rate'] = 0.0001
    config['batch_size'] = 500
    config['num_stacks'] = 4
    config['num_units'] = 512
    config['max_sentence_length'] = 32
    config['use_gpu'] = True
    config['num_epochs'] = 100
    # ---------------------- #

    # ------- paths -------- #
    config['vocab_path'] = 'lib/wlists/vocab.clc.min-count2.en'
    # config['data_path'] = 'lib/tsv/fcesplitpublic+bulats.nopunc.ged.spell.v3.tsv'
    config['data_path'] = 'lib/tsv/fcesplitpublic+bulats+ielts+fcesplit+cpe+cae.nopunc.ged.spell.v3.tsv'
    # config['data_path'] = 'lib/tsv/fake4.tsv'
    # ---------------------- #

    train(config)


if __name__ == '__main__':
    main()
