import logging
import matplotlib.pyplot
import numpy
import os
import time
import traceback

from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from typing import Union, Literal



logger = logging.getLogger(__name__)



def visualize(embeddings,
              labels         =None,
              method         ='tsne',
              random_state   =42,
              title          ='Embedding Visualization',
              annotate_points=True,
              tsne_perplexity=30.0,
              tsne_max_iter  =300,
              tsne_learning_rate: Union[float, Literal['auto']]='auto'):
    """
    Visualizes high-dimensional embeddings in 2D using t-SNE or PCA.

    Args:
        embeddings (list or numpy.array): A list or numpy array of embeddings.
                                       Each embedding should be a list or 1D array of numbers.
        labels (list, optional): A list of labels corresponding to each embedding.
                                 If provided, points on the plot will be annotated.
                                 Defaults to None.
        method (str, optional): Dimensionality reduction method.
                                'tsne' or 'pca'. Defaults to 'tsne'.
        random_state (int, optional): Random state for reproducibility of t-SNE/PCA.
                                      Defaults to 42.
        title (str, optional): The title of the plot.
                               Defaults to 'Embedding Visualization'.
        annotate_points (bool, optional): Whether to annotate points with labels if available.
                                          Defaults to True.
        tsne_perplexity (float, optional): The perplexity value for t-SNE.
                                           Relates to the number of nearest neighbors.
                                           Defaults to 30.0.
        tsne_max_iter (int, optional): Number of iterations for t-SNE optimization.
                                     Defaults to 300 (a smaller value for faster plotting,
                                     consider increasing for better results, e.g., 1000+).
        tsne_learning_rate (str or float, optional): Learning rate for t-SNE.
                                                    Can be 'auto' or a float.
                                                    Defaults to 'auto'.
    """
    if embeddings is None or len(embeddings) == 0:
        logger.error('Input embeddings list is empty or None.')
        return


    try:
        # Convert embeddings to numpy array
        embedding_array = numpy.array(embeddings)
        if embedding_array.ndim == 1: # Handle case of a single embedding
             logger.warning('Only one embedding provided. Visualization might not be meaningful.')
             # For a single point, we can't really do dimensionality reduction in a typical sense.
             # We'll plot it at (0,0) if it's reduced, or try to plot its first two dimensions.
             if embedding_array.shape[0] >= 2:
                 reduced_embeddings = numpy.array([[embedding_array[0], embedding_array[1]]])
             else: # Not enough dimensions to plot directly
                 reduced_embeddings = numpy.array([[0,0]]) # fallback
        elif embedding_array.shape[0] < 2 and method.lower() == 'tsne':
            logger.warning(f't-SNE requires at least 2 samples, but got {embedding_array.shape[0]}. Using PCA instead or plotting directly if 2D.')
            if embedding_array.shape[1] == 2: # Already 2D
                 reduced_embeddings = embedding_array
            elif embedding_array.shape[0] ==1 and embedding_array.shape[1] > 2 : # one sample many features
                 reduced_embeddings = numpy.array([[embedding_array[0,0], embedding_array[0,1]]]) # Plot first two components
            else: # Fallback for single high-D embedding
                 reduced_embeddings = numpy.array([[0,0]])
        elif embedding_array.shape[1] < 2:
            logger.error('Embeddings must have at least 2 dimensions for 2D visualization.')
            return
        elif embedding_array.shape[0] < embedding_array.shape[1] and method.lower() == 'tsne' and embedding_array.shape[0] <= tsne_perplexity:
             actual_perplexity = max(5.0, embedding_array.shape[0] - 1.0)
             logger.info(f'Perplexity ({tsne_perplexity}) is too high for the number of samples ({embedding_array.shape[0]}). '
                   f'Adjusting perplexity to {actual_perplexity}.')
             tsne_perplexity = actual_perplexity

        # Dimensionality Reduction
        if embedding_array.shape[0] > 1 and embedding_array.shape[1] > 2 : # Only reduce if more than 1 sample and more than 2D
            if method.lower() == 'tsne':
                tsne = TSNE(n_components=2,
                            random_state=random_state,
                            perplexity=tsne_perplexity,
                            max_iter=tsne_max_iter,
                            learning_rate=tsne_learning_rate,
                            init='pca', # pca init can be more stable
                            n_jobs=-4) # Use all available cores
                reduced_embeddings = tsne.fit_transform(embedding_array)
            elif method.lower() == 'pca':
                pca = PCA(n_components=2, random_state=random_state)
                reduced_embeddings = pca.fit_transform(embedding_array)
            else:
                logger.error(f"Unknown method '{method}'. Choose 'tsne' or 'pca'.")
                return
        elif embedding_array.shape[1] == 2: # Already 2D
            reduced_embeddings = embedding_array
        elif embedding_array.shape[0] == 1 and embedding_array.shape[1] >=2: # Single sample, plot its first two dimensions
             reduced_embeddings = numpy.array([[embedding_array[0,0], embedding_array[0,1]]])
        else: # Fallback for single 1D embedding or other edge cases
            logger.warning('Cannot perform standard dimensionality reduction. Plotting as is or with fallback.')
            if embedding_array.ndim == 1 and embedding_array.shape[0] >= 2:
                reduced_embeddings = numpy.array([[embedding_array[0], embedding_array[1]]])
            elif embedding_array.ndim == 2 and embedding_array.shape[1] == 1: # Multiple 1D embeddings
                # Create a synthetic second dimension (e.g., index or zeros)
                reduced_embeddings = numpy.hstack((embedding_array, numpy.arange(embedding_array.shape[0]).reshape(-1,1)))
            else: # True fallback
                reduced_embeddings = numpy.array([[0,0]]) if embedding_array.ndim == 1 else numpy.zeros((embedding_array.shape[0], 2))

    except Exception as e:
        logger.error(f'An error occurred during dimensionality reduction: {e}')
        return

    # Plotting
    try:
        matplotlib.pyplot.figure(figsize=(12, 10))

        if reduced_embeddings.ndim == 1:
            if reduced_embeddings.shape[0] >= 2:
                 logger.info('Plotting 1D reduced data against indices.')
                 x_coords = reduced_embeddings
                 y_coords = numpy.arange(reduced_embeddings.shape[0])
            elif reduced_embeddings.shape[0] == 1:
                 x_coords = numpy.array([reduced_embeddings[0]])
                 y_coords = numpy.array([0.0])
            else:
                 logger.error('Reduced embeddings are empty after 1D check.')
                 matplotlib.pyplot.close() # Close the figure if error
                 return
        elif reduced_embeddings.shape[1] == 1:
            logger.info('Plotting 1D reduced data (single column) against indices.')
            x_coords = reduced_embeddings[:, 0]
            y_coords = numpy.arange(reduced_embeddings.shape[0])
        elif reduced_embeddings.shape[1] >= 2:
            x_coords = reduced_embeddings[:, 0]
            y_coords = reduced_embeddings[:, 1]
        else:
            logger.error('Reduced embeddings do not have 1 or 2 dimensions for plotting.')
            matplotlib.pyplot.close() # Close the figure if error
            return

        matplotlib.pyplot.scatter(x_coords, y_coords, alpha=0.7)
        matplotlib.pyplot.title(title, fontsize=16)
        matplotlib.pyplot.xlabel('Dimension 1', fontsize=12)
        matplotlib.pyplot.ylabel('Dimension 2', fontsize=12)
        matplotlib.pyplot.grid(True, linestyle='--', alpha=0.6)

        if labels and annotate_points:
            if len(labels) == len(x_coords):
                for i, label in enumerate(labels):
                    matplotlib.pyplot.annotate(label, (x_coords[i], y_coords[i]),
                                 textcoords='offset points', xytext=(5,5), ha='left', fontsize=9)
            else:
                logger.warning(f'Number of labels ({len(labels)}) does not match number of plotted points '
                      f'({len(x_coords)}). Annotations will be skipped.')

        # --- MODIFICATION: Save instead of show ---
        plot_dir = 'embedding_plots'
        if not os.path.exists(plot_dir):
            os.makedirs(plot_dir)
        
        # Create a somewhat unique filename
        safe_title = "".join(c if c.isalnum() else "_" for c in title)
        timestamp = time.strftime('%Y%m%d-%H%M%S')
        filename = os.path.join(plot_dir, f'{safe_title}_{timestamp}.png')
        
        matplotlib.pyplot.savefig(filename)
        logger.info(f'Plot saved to {filename}')
        matplotlib.pyplot.close() # Close the figure object to free memory

    except Exception as e:
        logger.error(f'An error occurred during plotting: {e}')
        traceback.print_exc()
        if matplotlib.pyplot.gcf().get_axes(): # Check if a figure is active
            matplotlib.pyplot.close() # Attempt to close it
