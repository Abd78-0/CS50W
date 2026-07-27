from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse


from .models import User, Listing, Bid, Comment, Watchlist


def index(request):
    listings = Listing.objects.filter(is_active=True)
    watchlist_ids = set()

    if request.user.is_authenticated:
        watchlist_ids = set(request.user.watchlist.values_list("listing_id", flat=True))

    return render(request, "auctions/index.html", {
        "listings": listings,
        "comments": Comment.objects.all(),
        "watchlist_ids": watchlist_ids
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

    watchlisted = False
    user_has_won = False
    if request.user.is_authenticated:
        watchlisted = listing.watchlisted_by.filter(user=request.user).exists()
        user_has_won = listing.is_active is False and listing.winner_id == request.user.id

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "watchlisted": watchlisted,
        "user_has_won": user_has_won,
    })


@login_required
def create_listing(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        starting_bid = request.POST.get("starting_bid", "")
        image_url = request.POST.get("image_url", "")
        category = request.POST.get("category", "").strip()

        if not title or not description or not starting_bid:
            return render(request, "auctions/create_listing.html", {
                "message": "Title, description, and starting bid are required."
            })

        try:
            starting_bid_value = Decimal(starting_bid)
        except InvalidOperation:
            return render(request, "auctions/create_listing.html", {
                "message": "Starting bid must be a valid number."
            })

        listing = Listing(
            title=title,
            description=description,
            starting_bid=starting_bid_value,
            image_url=image_url or None,
            category=category or None,
            owner=request.user
        )
        listing.save()

        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/create_listing.html")
    

def watchlist(request):
    if request.user.is_authenticated:
        user_watchlist = Listing.objects.filter(watchlisted_by__user=request.user)
        return render(request, "auctions/watchlist.html", {
            "watchlist": user_watchlist
        })
    else:
        return HttpResponseRedirect(reverse("login"))
    

def categories(request):
    categories = Listing.objects.exclude(category__isnull=True).exclude(category="").values_list('category', flat=True).distinct()

    return render(request, "auctions/categories.html", {
        "categories": categories
    })


def category_listings(request, category_name):
    listings = Listing.objects.filter(category=category_name, is_active=True)

    return render(request, "auctions/category_listings.html", {
        "category_name": category_name,
        "listings": listings
    })


@login_required
def place_bid(request, listing_id):
    if request.method == "POST":
        try:
            bid_amount = Decimal(request.POST.get("bid_amount", ""))
        except InvalidOperation:
            return render(request, "auctions/listing.html", {
                "listing": Listing.objects.get(pk=listing_id),
                "error_message": "Please enter a valid bid amount."
            })

        listing = get_object_or_404(Listing, pk=listing_id)
        if not listing.is_active:
            return HttpResponseRedirect(reverse("listing", args=[listing_id]))

        current_highest_bid = listing.current_highest_bid()
        if listing.bids.exists():
            minimum_required = current_highest_bid
            if bid_amount <= minimum_required:
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "error_message": "Your bid must be at least the starting bid and greater than the current highest bid."
                })
        elif bid_amount < listing.starting_bid:
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "error_message": "Your bid must be at least the starting bid."
            })

        bid = Bid(amount=bid_amount, listing=listing, bidder=request.user)
        bid.save()
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


@login_required
def toggle_watchlist(request, listing_id):
    if request.method == "POST":
        listing = get_object_or_404(Listing, pk=listing_id)
        watchlist_item = Watchlist.objects.filter(user=request.user, listing=listing).first()

        if watchlist_item is None:
            Watchlist.objects.create(user=request.user, listing=listing)
        else:
            watchlist_item.delete()

    return HttpResponseRedirect(reverse("listing", args=[listing_id]))


@login_required
def close_listing(request, listing_id):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))

    listing = get_object_or_404(Listing, pk=listing_id)
    if listing.owner != request.user:
        raise PermissionDenied

    highest_bid = listing.bids.order_by('-amount', '-created_at').first()
    listing.is_active = False
    listing.winner = highest_bid.bidder if highest_bid else None
    listing.save()
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))