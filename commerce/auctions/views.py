from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from sympy import Max
from sympy import Max

from .models import User,Listing, Bid, Comment


def index(request):
    listings = Listing.objects.filter(is_active=True)

    return render(request, "auctions/index.html", {
        "listings": listings,
        "comments": Comment.objects.all()
    })


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def listing(request, listing_id):
    try:
        listing = Listing.objects.get(pk=listing_id)
    except Listing.DoesNotExist:
        return HttpResponse("Listing not found.", status=404)

    return render(request, "auctions/listing.html", {
        "listing": listing
    })


def create_listing(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        starting_bid = request.POST["starting_bid"]
        image_url = request.POST.get("image_url", "")
        category = request.POST.get("category", "")

        listing = Listing(
            title=title,
            description=description,
            starting_bid=starting_bid,
            image_url=image_url,
            category=category,
            owner=request.user
        )
        listing.save()

        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/create_listing.html")
    

def watchlist(request):
    if request.user.is_authenticated:
        user_watchlist = request.user.watchlist.all()
        return render(request, "auctions/watchlist.html", {
            "watchlist": user_watchlist
        })
    else:
        return HttpResponseRedirect(reverse("login"))
    

def categories(request):
    categories = Listing.objects.values_list('category', flat=True).distinct()

    return render(request, "auctions/categories.html", {
        "categories": categories
    })

def category_listings(request, category_name):  
    listings = Listing.objects.filter(category=category_name, is_active=True)

    return render(request, "auctions/category_listings.html", {
        "category_name": category_name,
        "listings": listings
    })

def place_bid(request, listing_id):
    if request.method == "POST":
        bid_amount = float(request.POST["bid_amount"])
        listing = Listing.objects.get(pk=listing_id)

        current_highest_bid = listing.current_highest_bid()
        if bid_amount > current_highest_bid:
            bid = Bid(
                amount=bid_amount,
                listing=listing,
                bidder=request.user
            )
            bid.save()
            return HttpResponseRedirect(reverse("listing", args=[listing_id]))
        else:
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "error_message": "Your bid must be higher than the current highest bid."
            })
    else:
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    

def current_highest_bid(self):
    highest = self.bids.order_by('-amount').first()
    return highest.amount if highest else self.starting_bid


def comment(request, listing_id):
    if request.method == "POST":
        content = request.POST["content"]
        listing = Listing.objects.get(pk=listing_id)

        comment = Comment(
            content=content,
            listing=listing,
            commenter=request.user
        )
        comment.save()
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    else:
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    

@login_required
def add_comment(request, listing_id):
    if request.method == "POST":
        content = request.POST["content"]
        listing = Listing.objects.get(pk=listing_id)

        comment = Comment(
            content=content,
            listing=listing,
            commenter=request.user
        )
        comment.save()
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    else:
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))