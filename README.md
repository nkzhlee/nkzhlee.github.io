# Zhaohui Li website

Static GitHub Pages site. The primary pages are `index.html`, `publications/index.html`, `projects/index.html`, and `blog/index.html`, styled by `css/site.css`.

The current CV is `files/Zhaohui_Li_CV.pdf`. Its editable LaTeX source is `cv-source/main.tex`, copied from the Career project in September 2026. To rebuild it with Tectonic:

```sh
tectonic cv-source/main.tex -o files
mv files/main.pdf files/Zhaohui_Li_CV.pdf
```

The portrait at `files/zhaohui-2026.jpg` is the original photo supplied by Zhaohui Li. It is cropped only by CSS in the hero layout.

The custom domain remains configured in `CNAME`. HTTPS for that domain requires attention in the GitHub Pages and DNS settings; it is not controlled by these static files.
