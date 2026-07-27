from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Bid, Comment, Listing, Watchlist


class AuctionFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="alice", password="secret123")
        self.other_user = get_user_model().objects.create_user(username="bob", password="secret123")
        self.listing = Listing.objects.create(
            title="Vintage Lamp",
            description="A working vintage lamp",
            starting_bid=50,
            owner=self.user,
        )

    def test_user_can_add_and_view_watchlist(self):
        self.client.login(username="alice", password="secret123")

        response = self.client.post(reverse("toggle_watchlist", args=[self.listing.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Watchlist.objects.filter(user=self.user, listing=self.listing).exists())

        watchlist_response = self.client.get(reverse("watchlist"))
        self.assertContains(watchlist_response, self.listing.title)

    def test_owner_can_close_listing(self):
        self.client.login(username="alice", password="secret123")

        response = self.client.post(reverse("close_listing", args=[self.listing.id]))

        self.assertEqual(response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertFalse(self.listing.is_active)

    def test_non_owner_cannot_close_listing(self):
        self.client.login(username="bob", password="secret123")

        response = self.client.post(reverse("close_listing", args=[self.listing.id]))

        self.assertEqual(response.status_code, 403)
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_active)

    def test_bid_must_be_at_least_starting_bid_and_higher_than_current_highest(self):
        self.client.login(username="bob", password="secret123")
        Bid.objects.create(amount=60, bidder=self.user, listing=self.listing)

        low_bid_response = self.client.post(reverse("place_bid", args=[self.listing.id]), {"bid_amount": 55})
        self.assertEqual(low_bid_response.status_code, 200)
        self.assertContains(low_bid_response, "at least")
        self.assertEqual(self.listing.bids.count(), 1)

        valid_bid_response = self.client.post(reverse("place_bid", args=[self.listing.id]), {"bid_amount": 61})
        self.assertEqual(valid_bid_response.status_code, 302)
        self.assertEqual(self.listing.bids.count(), 2)
        self.assertEqual(self.listing.bids.latest("created_at").bidder, self.other_user)

    def test_user_can_post_comment_and_view_it_on_listing_page(self):
        self.client.login(username="alice", password="secret123")

        response = self.client.post(reverse("add_comment", args=[self.listing.id]), {"content": "Love this listing!"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(listing=self.listing, content="Love this listing!").exists())

        listing_page = self.client.get(reverse("listing", args=[self.listing.id]))
        self.assertContains(listing_page, "Love this listing!")
