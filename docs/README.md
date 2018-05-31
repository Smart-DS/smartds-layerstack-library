The documentation is built with [Sphinx](http://sphinx-doc.org/index.html). There are several steps to creating and publishing the documentation:

1. Convert .md input files to .rst
2. Build the HTML docs
3. Push to GitHub

### Markdown to reStructuredText

Markdown files are registered in `docs/source/md_files.txt`. Paths in that file should be relative to the docs folder and should exclude the file extension. For every file listed there, the `dev/md_to_rst.py` utility will expect to find a markdown (`.md`) file, and will look for an optional `.postfix` file, which is expected to contain `.rst` code to be appended to the `.rst` file created by converting the input `.md` file. Thus, running `dev/md_to_rst.py` on the `docs/source/md_files.txt` file will create revised `.rst` files, one for each entry listed in the registry. In summary:

```
cd docs/source
python ../../dev/md_to_rst.py md_files.txt
```

### Building HTML Docs

Run `make html` for Mac and Linux; `make.bat html` for Windows.

### Pushing to GitHub Pages

#### Mac/Linux

```
make github
```

#### Windows

```
make.bat html
```

Then run the github-related commands by hand:

```
git branch -D gh-pages
git push origin --delete gh-pages
ghp-import -n -b gh-pages -m "Update documentation" ./build/html
git checkout gh-pages
git push origin gh-pages
git checkout master # or whatever branch you were on
```