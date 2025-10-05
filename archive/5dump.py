from macapptree import get_tree, get_tree_screenshot, get_app_bundle
from pprint import pprint
from PIL import Image

bundle = get_app_bundle("System Settings")
tree, im, im_seg = get_tree_screenshot(bundle)
# `tree` is a dictionary of the accessibility hierarchy
# `im` is a cropped PIL.Image of the app window
# `im_seg` is a PIL.Image with bounding boxes by element type
#pprint(tree)

pprint(im)
pprint(tree)
pprint(im_seg)
im.save("im.png")
im_seg.save("im_seg.png")