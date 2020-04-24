import pandas as pd
import networkx as nx

# load data
categories = pd.read_csv("categories.csv")
products = pd.read_csv("products.csv")
transactions = pd.read_csv("transactions.csv")

# convert categories dataframe to directed graph (child category -> parent category)
G = nx.from_pandas_edgelist(categories, 'Category', 'Parent Category', create_using=nx.DiGraph)
# node is a leaf (end of branch) if it has no outgoing edges
leaves = [node for node in G if G.out_degree(node)==0]

########
#below section converts the graph to a dataframe with columns representing the top-most category and all sub-categories (can be more than one)
data = []
for node in G:
    if G.in_degree(node) == 0:
        for leaf in leaves:
            try:
                # finds path from node with no inputs (bottom-most category) to leaf (top-most category)
                data.append(nx.shortest_path(G, node, leaf))
            except:
                pass

categories = pd.DataFrame(data, columns=['Category0', 'Category1', 'Category2', 'Category3'])
########

def find_leaf(G,parent):
    ''' Given a graph and a node, return the leaf at the end of branch'''
    child = list(nx.descendants(G,parent))
    if len(child) == 0:
        return parent
    else:
        return find_leaf(G, child[0])

# find top-most category for each product
products['Parent Category'] = products.apply(lambda row: find_leaf(G, row['Category']), axis=1)
# mean price (across all categories)
mean_price = products['Price'].mean()
# find mean and count per category
mean_count = products.groupby('Parent Category').agg({"Price": ['mean', 'count']})

# merge transactions with products based on 'Product ID' columns
transactions = transactions.merge(products, on='Product ID', how='left')
# find total value of transaction
transactions['Value'] = transactions['Quantity']*transactions['Price']
# find total value per category
transaction_value = transactions.groupby('Parent Category').agg({"Value": sum})

# merge mean_count and transaction_value dataframes
results = pd.merge(mean_count,transaction_value, left_index=True, right_index=True)

# rename axes and columns
results = results.rename_axis('Category')
results.columns = ['Average Price', 'Number of Products', 'Total Value']

# add row with data for all categories
results.loc['All categories'] = [mean_price, sum(results['Number of Products']), sum(results['Total Value'])]
# round floats to 2 decimal places
results = results.round({'Average Price':2, 'Total Value':2})

# save result to CSV
results.to_csv('results.csv')
