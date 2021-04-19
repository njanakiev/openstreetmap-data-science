import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


def visualize_graph(embedding, precision_matrix, names, labels, textsize=10):
    """Visualize Graph on embedding by using the precision matrix. Code adapted from: 
    http://scikit-learn.org/stable/auto_examples/applications/plot_stock_market.html
    """
    
    n_labels = labels.max()
    plt.axis('off')

    # Display a graph of the partial correlations
    partial_correlations = precision_matrix.copy()
    d = 1 / np.sqrt(np.diag(partial_correlations))
    partial_correlations *= d
    partial_correlations *= d[:, np.newaxis]
    non_zero = (np.abs(np.triu(partial_correlations, k=1)) > 0.02)

    # Plot the nodes using the coordinates of our embedding
    plt.scatter(embedding[:, 0], embedding[:, 1], s=100 * d ** 2, c=labels,
                cmap=plt.cm.Spectral)

    # Plot the edges
    start_idx, end_idx = np.where(non_zero)
    # a sequence of (*line0*, *line1*, *line2*), where::
    #            linen = (x0, y0), (x1, y1), ... (xm, ym)
    segments = [[embedding[start], embedding[stop]]
                for start, stop in zip(start_idx, end_idx)]
    values = np.abs(partial_correlations[non_zero])
    lc = LineCollection(segments,
                        zorder=0, cmap=plt.cm.summer_r,
                        norm=plt.Normalize(0, .7 * values.max()))
    lc.set_array(values)
    lc.set_linewidths(15 * values)
    plt.gca().add_collection(lc)

    # Add a label to each node. The challenge here is that we want to
    # position the labels to avoid overlap with other labels
    for index, (name, label, (x, y)) in enumerate(
            zip(names, labels, embedding)):

        dx = x - embedding[:, 0]
        dx[index] = 1
        dy = y - embedding[:, 1]
        dy[index] = 1
        this_dx = dx[np.argmin(np.abs(dy))]
        this_dy = dy[np.argmin(np.abs(dx))]
        if this_dx > 0:
            horizontalalignment = 'left'
            x = x + .002
        else:
            horizontalalignment = 'right'
            x = x - .002
        if this_dy > 0:
            verticalalignment = 'bottom'
            y = y + .002
        else:
            verticalalignment = 'top'
            y = y - .002
        plt.text(x, y, name, size=textsize,
                 horizontalalignment=horizontalalignment,
                 verticalalignment=verticalalignment,
                 bbox=dict(facecolor='w',
                           edgecolor=plt.cm.Spectral(label / float(n_labels)),
                           alpha=.6))

    plt.xlim(embedding[:, 0].min() - .15 * embedding[:, 0].ptp(),
             embedding[:, 0].max() + .10 * embedding[:, 0].ptp(),)
    plt.ylim(embedding[:, 1].min() - .03 * embedding[:, 1].ptp(),
             embedding[:, 1].max() + .03 * embedding[:, 1].ptp())

    plt.axis('equal')
