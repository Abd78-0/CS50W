from django.shortcuts import render, redirect
import markdown2 as md
import random
from . import util



def index(request):
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries()
    })

def entry(request, title):
    file = util.get_entry(title)
    if file is None:
        return render(request, "encyclopedia/error.html", {
            "error": f"Entry '{title}' not found."
        })

    html = md.markdown(file)
    return render(request, "encyclopedia/entry.html", {
        "title": title,
        "content": html
    })


'''
def entry(request, title):
    try:
        file = util.get_entry(title)
        html = md.markdown(file)

        return render(request, "encyclopedia/entry.html", {
            "title": title,
            "content": html
        })
    except:
        return render(request, "encyclopedia/error.html")
'''

def search(request):
    searchkey = request.GET.get("q", "").strip()
    file = util.get_entry(searchkey)
    if file:
        html = md.markdown(file)
        return render(request, "encyclopedia/entry.html", {
            "title": searchkey,
            "content": html
        })
    else:
        entries = util.list_entries()
        matched_entries = [entry for entry in entries if searchkey.lower() in entry.lower()]
        return render(request, "encyclopedia/search.html", {
            "matched_entries": matched_entries,
            "query": searchkey
        })

def newPage(request):
    if request.method == "POST":
        title = request.POST.get("newTitle", "").strip()
        existing_entries = util.list_entries()
        if title.lower() in [entry.lower() for entry in existing_entries]:
            return render(request, "encyclopedia/error.html", {
                "error": "Entry already exists"
            })

        newContent = request.POST.get("newContent", "")

        with open(f"entries/{title}.md", "w", encoding="utf-8") as f:
            f.write(newContent)

        return redirect("entry", title=title)
        


    return render(request, "encyclopedia/newPage.html")


def editPage(request, title):
    if request.method == "POST":
        newContent = request.POST.get("newContent", "").strip()

        with open(f"entries/{title}.md", "w", encoding="utf-8") as f:
            f.write(newContent)

        return redirect("entry", title=title)

    current_content= util.get_entry(title)
    return render(request, "encyclopedia/editPage.html", {
        "title": title,
        "current_content": current_content
    })

def randomPage(request):
    entries = util.list_entries()
    if entries:
        random_entry = random.choice(entries)
        return redirect("entry", title=random_entry)