from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import re
import urllib2
import urlparse 
import cPickle
from bs4 import BeautifulSoup


DERMNET_PIC_PAGE = "http://www.dermnet.com/dermatology-pictures-skin-disease-pictures/"
DERMNET_HOME_PAGE = "http://www.dermnet.com/"


def genClass2URL():
   
    soup = soupify(DERMNET_PIC_PAGE)
    class_links = soup.find("table").find_all("a")
    n_links = len(class_links)
    print("Found {} total image classes.".format(n_links))
    n_total = 0

    img_dict = {}
    for i, link in enumerate(class_links):
        abs_link = urlparse.urljoin(DERMNET_HOME_PAGE, link.get('href'))
        class_name = re.sub(r'[^a-z0-9A-Z\s]+', '', link.string)
        print('\nFetching URLs for class [{}/{}]: {}'.format(i + 1, n_links, class_name))
        class_images = genClassImages(abs_link)
        n_total += len(class_images)
        print('Fetched {} images. Total of {} images.'.format(len(class_images), n_total))
        img_dict[class_name] = class_images

    return img_dict


def genClassImages(class_url):
   
    images = []
    urls = genClassCategories(class_url)
    print('- Found {} total sub-classes for class.'.format(len(urls)))

    for i, url in enumerate(urls):
        print('-- Fetching images from sub-class [{}/{}]'.format(i + 1, len(urls)))
        images.extend(genCategoryImages(url))
    
    return images


def genClassCategories(class_url):
   
    soup = soupify(class_url)
    links = soup.find("table").find_all("a")
    
    categories = []
    for link in links:
        abs_link = urlparse.urljoin(DERMNET_HOME_PAGE, link.get('href'))
        categories.append(abs_link)
    return categories


def genCategoryImages(cat_url):
    
        images = []
    genPageImages(cat_url, images)
    
    thumb_urls = genCategoryLinks(cat_url)    
    for page in thumb_urls:
        genPageImages(page, images)
    
    return images


def genCategoryLinks(url):
    
    soup = soupify(url)
    pages = soup.find("div", "pagination")
    thumb_urls = []
    
    if pages:  
        for page in pages:
            if page.name == 'a' and page.string != 'Next':
                page_url = urlparse.urljoin(DERMNET_HOME_PAGE, page['href'])
                thumb_urls.append(page_url)
    
    return thumb_urls


def genPageImages(url, image_list):
    
    soup = soupify(url)
    thumbnails = soup.find_all("div","thumbnails")
    if thumbnails: 
        for thumb in thumbnails:
            thumb_link = thumb.img['src']
            image_link = re.sub(r'Thumb',"",thumb_link)
            image_list.append(image_link)


def soupify(url):
    
    html = urllib2.urlopen(url)
    soup = BeautifulSoup(html, "lxml")
    return soup


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('out_folder', type=str, help='where to store scraped images.')
    parser.add_argument('--dictionary', type=str, help='class2url dictionary path')
    args = parser.parse_args()

    print('Scraping DermNet for URLs.')
    if args.dictionary:
        with open(args.dictionary, 'rb') as fp:
            image_dict = cPickle.load(fp)
    else:
        image_dict = genClass2URL()

    n_images = 0
    for klass, images in image_dict.iteritems():
        n_images += len(images)

    n_downloaded = 0

    with open(os.path.join(args.out_folder, 'backup.pkl'),'wb') as fp:
        cPickle.dump(image_dict, fp)
    print('Dumped dictionary of URLs to current directory.')

    for klass, images in image_dict.iteritems():
        class_path = os.path.join(args.out_folder, klass)
        if not os.path.exists(class_path):
            os.mkdir(class_path)

        for image in images:
            image_name = os.path.basename(image)
            file_name = os.path.join(class_path, image_name)
            try:
                f = urllib2.urlopen(image).read()
                open(file_name, 'wb').write(f)
                n_downloaded += 1
                print('Downloaded [{}/{}] images.'.format(n_downloaded, n_images))
            except urllib2.HTTPError:
continue