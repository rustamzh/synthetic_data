import os
import sys
import numpy as np
import pickle as pkl
import pandas as pd
import seaborn as sns
import scipy.stats as stats
from sklearn import metrics
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
from sklearn.utils import shuffle
from sklearn.decomposition import PCA as PCA
from sklearn.manifold import TSNE
from sklearn.externals import joblib
from sklearn.neighbors import NearestNeighbors

class LossPlot():
	""" 
	Uses `matplotlib` and `seaborn` to plot the test loss, 
	generator loss, discriminator loss across several epochs.

	Parameters
	----------
	log_file : string, required
		The pickle file with all the log values generated by
		HealthGAN.
	"""

	def __init__(self, log_file):

		if not os.path.exists('gen_data'):
			os.makedirs('gen_data')

		if not os.path.exists('gen_data/plots'):
			os.makedirs('gen_data/plots')

		try:
			self.log = pkl.load(open(log_file, 'rb'))
		except:
			print("Please provide a correct pickle log file")

	def plot(self, savefig=False):
		"""
		Plot the loss graph.

		Parameters
		----------
		savefig: boolean, optional
			If set to True, the plots generated will be saved to disk.

		Outputs
		-------
		Produces a 8x8 figure for losses
		"""
		losses = ['test_loss', 'gen_loss', 'disc_loss', 'time']
		titles = ['Test Loss', 'Generator Loss', 'Discriminator Loss', 'Time per Epoch']

		pylab.rcParams['figure.figsize'] = 6, 6

		try:
			for i, loss in enumerate(losses):
				j = i%2
				if isinstance(self.log[loss][0], list):
					new_df = pd.DataFrame({titles[i]: [v[-1] for v in self.log[loss]]})
				else:
					new_df = pd.DataFrame({titles[i]: self.log[loss]})
				sns.lineplot(data=new_df, dashes=False, palette="hls")
				plt.title(titles[i])
				plt.xlabel('Epochs (in thousands)')
				if (savefig):
					plt.savefig('gen_data/plots/' + loss + '.png')
				plt.show()
				plt.close()
			if (savefig):
				print("Plots saved! Refer to the files 'time.png', test_loss.png', 'disc_loss.png' and 'gen_loss.png' inside 'gen_data/plots' folder.")
		except:
			print("Could not produce plots")

class AUCPlot():
	""" 
	Uses `matplotlib` and `seaborn` to plot the AUC curve

	Parameters
	----------
	train_file : string, required
		The training file to be used for generating the AUC Curve.
	test_file : string, required
		The testing file to be used for generating the AUC Curve.
	synth_file : string, required
		The synthetic data file to be used for generating the AUC Curve.
	name : string, required
		A name for the plot.
	"""
	def __init__(self, train_file, test_file, synth_file, name):

		if not os.path.exists('gen_data'):
			os.makedirs('gen_data')

		if not os.path.exists('gen_data/plots'):
			os.makedirs('gen_data/plots')

		data, labels = self.__create_shuffled_data(train_file, test_file)
		self.fpr, self.tpr, self.auc = self.__compute_auc(synth_file, data, labels)
		self.name = name

	def __create_shuffled_data(self, train_file, test_file)

	    # Read in train and test
	    train_set = pd.read_csv(train_file)
	    test_set = pd.read_csv(test_file)

	    # Create labels
	    label_train = np.empty(train_set.shape[0], dtype=int)
	    label_train.fill(-1)
	    label_test = np.empty(test_set.shape[0], dtype=int)
	    label_test.fill(1)

	    # Combine
	    labels = np.concatenate([label_train, label_test], axis=0)
	    data = pd.concat([train_set, test_set], axis=0)
	    data['labels'] = labels.tolist()

	    # Randomize
	    data = shuffle(data)
	    data, labels = (data.drop('labels', axis=1), data['labels'])

	    return data, labels

	def __compute_auc(self, synth_file, data, labels):
    
	    synth_data = pd.read_csv(synth_file)
	    
	    syn_dists = self.__nearest_neighbors(data, synth_data)
	    fpr, tpr, _ = metrics.roc_curve(labels, syn_dists)
	    roc_auc = metrics.auc(fpr, tpr)

	    return fpr, tpr, roc_auc

	def __nearest_neighbors(self, t, s):
	    """
	    Find nearest neighbors d_ts and d_ss
	    """

	    # Fit to S
	    nn_s = NearestNeighbors(1, n_jobs=-1).fit(s)
	   
	    # Find distances from t to s
	    d = nn_s.kneighbors(t)[0]
	    
	    return d

	def plot(self, savefig=False):
		""" 
		The function plots the AUC curve.
		  
		Parameters
		----------
		savefig: boolean, optional
			If set to True, the plots generated will be saved to disk.

		Outputs
		-------
		PCA Plot:
			Plots the AUC curve and saves the file as 
			`membership_inference_auc_{name}.png`
		"""

		pylab.rcParams['figure.figsize'] = 6, 6
	    plt.title('Receiver Operating Characteristic', fontsize=24)
	    plt.plot([0, 1], [0, 1], 'r--')
	    plt.plot(self.fpr, self.tpr, label=self.name)

	    plt.xlim([-0.05, 1.05])
	    plt.ylim([-0.05, 1.05])
	    plt.ylabel('True Positive Rate', fontsize=18)
	    plt.xlabel('False Positive Rate', fontsize=18)
	    if (savefig):
	    	plt.savefig(f'gen_data/membership_inference_auc_{self.name}.png')
	    plt.show()
	    if (savefig):
	    	print(f"The plot has been saved as membership_inference_auc_{self.name}.png inside gen_data/plots.")

class ComponentPlots():
	""" 
	Uses `matplotlib` and `seaborn` to plot PCA and TSNE plot
	for real and synthetic data files.
	"""

	def __init__(self):

		if not os.path.exists('gen_data'):
			os.makedirs('gen_data')

		if not os.path.exists('gen_data/plots'):
			os.makedirs('gen_data/plots')

	def pca_plot(self,
				 real_data,
				 synthetic_data=None, 
				 title="Two Component PCA",
				 savefig=False):
		""" 
		The function plots PCA between two components for 
		real and synthetic data.

		Parameters
		----------
		real_data : str, required
			The file which contains the real data.
		synthetic_data : str, optional
			The file which contains the synthetic data.
		title: str, optional
			The title of the plot.
		savefig: boolean, optional
			If set to True, the plots generated will be saved to disk.
		  
		Outputs
		-------
		PCA Plot:
			Plots the PCA components for the two datasets and 
			save file with the given name followed by '_real_syn'.
		"""

		real_data = pd.read_csv(real_data)
		if synthetic_data is not None:
			synthetic_data = pd.read_csv(synthetic_data)

		plt.style.use('seaborn-muted')
		pylab.rcParams['figure.figsize'] = 8, 8
		np.random.seed(1234)
		flatui = ["#34495e", "#e74c3c"]
		sns.set_palette(flatui)

		pca_orig = PCA(2)
		pca_orig_data = pca_orig.fit_transform(real_data)
		plt.scatter(*pca_orig_data.T, alpha=.3)

		plt.title(title, fontsize=24)
		plt.xlabel('First Component', fontsize=16)
		plt.ylabel('Second Component', fontsize=16)

		if synthetic_data is not None:
			pca_synth_data = pca_orig.transform(synthetic_data)
			plt.scatter(*pca_synth_data.T, alpha=.4)
			plt.legend(labels=['Original Data', 'Synthetic Data'])
			if (savefig):
				plt.savefig(f'gen_data/plots/{title}_real_syn.png')
			plt.show()
			if (savefig):
				print(f"PCA Plot generated as {title}_real_syn.png inside gen_data/plots.")
		else:
			plt.legend(labels=['Original Data'])
			if (savefig):
				plt.savefig(f'gen_data/plots/{title}_real.png')
			plt.show()
			if (savefig):
				print(f"PCA Plot generated as {title}_real.png inside gen_data/plots.")

	def combined_pca(self,
					 real_data, 
					 synthetic_datas, 
					 names,
					 savefig=False):
		""" 
		The function plots PCA between two components between
		real data and several synthetic datasets.

		Parameters
		----------
		real_data : str, required
			The file which contains the real data.
		synthetic_datas : list, required
			The list of files that contain synthetic data (max 6).
		names: list, required
			The titles for each plot.
		savefig: boolean, optional
			If set to True, the plots generated will be saved to disk.
		  
		Outputs
		-------
		PCA Plots:
			Plots the PCA components across a set of plots for each
			of the synthetic data files.
		"""

		plt.style.use('seaborn-muted')
		pylab.rcParams['figure.figsize'] = 8, 8
		np.random.seed(1234)
		flatui = ["#34495e", "#e74c3c"]
		sns.set_palette(flatui)

		real_data = pd.read_csv(real_data)

		fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(
			2, 3, sharey=True, sharex=True)

		pca_orig = PCA(2)
		pca_orig_data = pca_orig.fit_transform(real_data)

		axes = [ax1, ax2, ax3, ax4, ax5, ax6]

		# plot orig data
		for a in axes:
			a.scatter(*pca_orig_data.T, alpha=.3)

		pca_synth_data = []
		for s in synthetic_datas:
			s = pd.read_csv(s)
			pca_synth_data.append(pca_orig.transform(s))

		for i, a in enumerate(axes):
			if i < len(pca_synth_data):
				a.scatter(*(pca_synth_data[i]).T, alpha=.4)

			a.set_title(names[i], fontsize=16)

		fig.add_subplot(111, frameon=False)

		# Hide tick and tick label of the big axes
		plt.tick_params(labelcolor='none', 
						top='off', 
						bottom='off', 
						left='off', 
						right='off')
		plt.grid(False)
		plt.xlabel("First Component", fontsize=18)
		plt.ylabel("Second Component", fontsize=18)

		if (savefig):
			plt.savefig(f'gen_data/plots/combined_pca.png')
		plt.show()
		if (savefig):
			print(f"PCA Plot generated as combined_pca.png inside gen_data/plots.")

	def combined_tsne(self,
					 real_data, 
					 synthetic_datas, 
					 names,
					 savefig=False):

		""" 
		The function plots t-distributed Stochastic Neighbor Embedding 
		between two components for real and several synthetic datasets.

		Parameters
		----------
		real_data : str, required
			The file which contains the real data.
		synthetic_datas : list, required
			The list of files that contain synthetic data (max 6).
		names: list, required
			The titles for each plot.
		savefig: boolean, optional
			If set to True, the plots generated will be saved to disk.

		Outputs
		-------
		PCA Plots:
			Plots the PCA components across a set of plots for each
			of the synthetic data files.
		"""

		plt.style.use('seaborn-muted')
		pylab.rcParams['figure.figsize'] = 8, 8
		np.random.seed(1234)
		flatui = ["#34495e", "#e74c3c"]
		sns.set_palette(flatui)

		real_data = pd.read_csv(real_data)

		fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(
			2, 3, sharey=True, sharex=True)

		tsne_orig = TSNE(n_components=2)
		tsne_orig_data = tsne_orig.fit_transform(real_data)

		axes = [ax1, ax2, ax3, ax4, ax5, ax6]

		# plot orig data
		for a in axes:
			a.scatter(*tsne_orig_data.T, alpha=.3)

		tsne_synth_data = []
		for s in synthetic_datas:
			s = pd.read_csv(s)
			tsne_synth_data.append(tsne_orig.fit_transform(s))

		for i, a in enumerate(axes):
			if i < len(tsne_synth_data):
				a.scatter(*(tsne_synth_data[i]).T, alpha=.4)

			a.set_title(names[i], fontsize=16)

		fig.add_subplot(111, frameon=False)

		# Hide tick and tick label of the big axes
		plt.tick_params(labelcolor='none', 
						top='off', 
						bottom='off', 
						left='off', 
						right='off')
		plt.grid(False)
		plt.xlabel("First Component", fontsize=18)
		plt.ylabel("Second Component", fontsize=18)

		if (savefig):
			plt.savefig(f'gen_data/plots/combined_tsne.png')
		plt.show()
		if (savefig):
		print(f"PCA Plot generated as combined_tsne.png inside gen_data/plots.")