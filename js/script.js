/**
 * WEBSITE: https://themefisher.com
 * TWITTER: https://twitter.com/themefisher
 * FACEBOOK: https://facebook.com/themefisher
 * GITHUB: https://github.com/themefisher/
 */

jQuery(function ($) {
	'use strict';

	/* ----------------------------------------------------------- */
	/*  Fixed header
	/* ----------------------------------------------------------- */
	$(window).on('scroll', function () {

		// fixedHeader on scroll
		function fixedHeader() {
			var headerTopBar = $('.top-bar').outerHeight();
			var headerOneTopSpace = $('.header-one .logo-area').outerHeight();

			var headerOneELement = $('.header-one .site-navigation');
			var headerTwoELement = $('.header-two .site-navigation');

			if ($(window).scrollTop() > headerTopBar + headerOneTopSpace) {
				$(headerOneELement).addClass('navbar-fixed');
				$('.header-one').css('margin-bottom', headerOneELement.outerHeight());
			} else {
				$(headerOneELement).removeClass('navbar-fixed');
				$('.header-one').css('margin-bottom', 0);
			}
			if ($(window).scrollTop() > headerTopBar) {
				$(headerTwoELement).addClass('navbar-fixed');
				$('.header-two').css('margin-bottom', headerTwoELement.outerHeight());
			} else {
				$(headerTwoELement).removeClass('navbar-fixed');
				$('.header-two').css('margin-bottom', 0);
			}
		}
		fixedHeader();


		// Count Up
		function counter() {
			var oTop;
			if ($('.counterUp').length !== 0) {
				oTop = $('.counterUp').offset().top - window.innerHeight;
			}
			if ($(window).scrollTop() > oTop) {
				$('.counterUp').each(function () {
					var $this = $(this),
						countTo = $this.attr('data-count');
					$({
						countNum: $this.text()
					}).animate({
						countNum: countTo
					}, {
						duration: 1000,
						easing: 'swing',
						step: function () {
							$this.text(Math.floor(this.countNum));
						},
						complete: function () {
							$this.text(this.countNum);
						}
					});
				});
			}
		}
		counter();


		// scroll to top btn show/hide
		function scrollTopBtn() {
			var scrollToTop = $('#back-to-top'),
				scroll = $(window).scrollTop();
			if (scroll >= 50) {
				scrollToTop.fadeIn();
			} else {
				scrollToTop.fadeOut();
			}
		}
		scrollTopBtn();
	});


	$(document).ready(function () {

		// navSearch show/hide
		function navSearch() {
			$('.nav-search').on('click', function () {
				$('.search-block').fadeIn(350);
			});
			$('.search-close').on('click', function () {
				$('.search-block').fadeOut(350);
			});
		}
		navSearch();

		// navbarDropdown
		function navbarDropdown() {
			if ($(window).width() < 992) {
				$('.site-navigation .dropdown-toggle').on('click', function () {
					$(this).siblings('.dropdown-menu').animate({
						height: 'toggle'
					}, 300);
				});

				var navbarHeight = $('.site-navigation').outerHeight();
				$('.site-navigation .navbar-collapse').css('max-height', 'calc(100vh - ' + navbarHeight + 'px)');
			}
		}
		navbarDropdown();


		// back to top
		function backToTop() {
			$('#back-to-top').on('click', function () {
				$('#back-to-top').tooltip('hide');
				$('body,html').animate({
					scrollTop: 0
				}, 800);
				return false;
			});
		}
		backToTop();


		// banner-carousel
		function bannerCarouselOne() {
			$('.banner-carousel.banner-carousel-1').slick({
				slidesToShow: 1,
				slidesToScroll: 1,
				autoplay: true,
				dots: true,
				speed: 600,
				arrows: true,
				prevArrow: '<button type="button" class="carousel-control left" aria-label="carousel-control"><i class="fas fa-chevron-left"></i></button>',
				nextArrow: '<button type="button" class="carousel-control right" aria-label="carousel-control"><i class="fas fa-chevron-right"></i></button>'
			});
			$('.banner-carousel.banner-carousel-1').slickAnimation();
		}
		bannerCarouselOne();


		// banner Carousel Two
		function bannerCarouselTwo() {
			$('.banner-carousel.banner-carousel-2').slick({
				fade: true,
				slidesToShow: 1,
				slidesToScroll: 1,
				autoplay: true,
				dots: false,
				speed: 600,
				arrows: true,
				prevArrow: '<button type="button" class="carousel-control left" aria-label="carousel-control"><i class="fas fa-chevron-left"></i></button>',
				nextArrow: '<button type="button" class="carousel-control right" aria-label="carousel-control"><i class="fas fa-chevron-right"></i></button>'
			});
		}
		bannerCarouselTwo();


		// pageSlider
		function pageSlider() {
			$('.page-slider').slick({
				fade: true,
				slidesToShow: 1,
				slidesToScroll: 1,
				autoplay: true,
				dots: false,
				speed: 600,
				arrows: true,
				prevArrow: '<button type="button" class="carousel-control left" aria-label="carousel-control"><i class="fas fa-chevron-left"></i></button>',
				nextArrow: '<button type="button" class="carousel-control right" aria-label="carousel-control"><i class="fas fa-chevron-right"></i></button>'
			});
		}
		pageSlider();


		// Shuffle js filter and masonry
		function projectShuffle() {
			if ($('.shuffle-wrapper').length !== 0) {
				var Shuffle = window.Shuffle;
				var myShuffle = new Shuffle(document.querySelector('.shuffle-wrapper'), {
					itemSelector: '.shuffle-item',
					sizer: '.shuffle-sizer',
					buffer: 1
				});
                myShuffle.filter('commute-booster');
                
                function playVisibleProjectVideos() {
                  document.querySelectorAll('#project-area .shuffle-item video').forEach(function (v) {
                    // only try to play videos that are actually visible
                    var el = v.closest('.shuffle-item');
                    if (!el) return;
                    if (el.offsetParent === null) return;

                    try {
                      v.muted = true;
                      v.playsInline = true;
                      var p = v.play();
                      if (p && typeof p.catch === 'function') p.catch(function () {});
                    } catch (e) {}
                  });
                }

                // run after initial filter + layout has applied
                setTimeout(playVisibleProjectVideos, 200);



				$('input[name="shuffle-filter"]').on('change', function (evt) {
					var input = evt.currentTarget;
					if (input.checked) {
						myShuffle.filter(input.value);
                        setTimeout(playVisibleProjectVideos, 120);

					}
				});
				$('.shuffle-btn-group label').on('click', function () {
					$('.shuffle-btn-group label').removeClass('active');
					$(this).addClass('active');
				});
			}
		}
		projectShuffle();


		// testimonial carousel
		function testimonialCarousel() {
			$('.testimonial-slide').slick({
				slidesToShow: 1,
				slidesToScroll: 1,
				dots: true,
				speed: 600,
				arrows: false
			});
		}
		testimonialCarousel();


		// team carousel
		function teamCarousel() {
			$('.team-slide').slick({
				dots: false,
				infinite: false,
				speed: 300,
				slidesToShow: 4,
				slidesToScroll: 2,
				arrows: true,
				prevArrow: '<button type="button" class="carousel-control left" aria-label="carousel-control"><i class="fas fa-chevron-left"></i></button>',
				nextArrow: '<button type="button" class="carousel-control right" aria-label="carousel-control"><i class="fas fa-chevron-right"></i></button>',
				responsive: [{
						breakpoint: 992,
						settings: {
							slidesToShow: 3,
							slidesToScroll: 3
						}
					},
					{
						breakpoint: 768,
						settings: {
							slidesToShow: 2,
							slidesToScroll: 2
						}
					},
					{
						breakpoint: 481,
						settings: {
							slidesToShow: 1,
							slidesToScroll: 1
						}
					}
				]
			});
		}
		teamCarousel();


		// media popup
		function mediaPopup() {
			$('.gallery-popup').colorbox({
				rel: 'gallery-popup',
				transition: 'slideshow',
				innerHeight: '500'
			});
			$('.popup').colorbox({
				iframe: true,
				innerWidth: 600,
				innerHeight: 400
			});
		}
		mediaPopup();

	});


});


/* ============================
   Click-to-play behavior (no layout changes)
   - Click any tile: plays/pauses that tile
   - Keeps others paused
   ============================ */

(function () {
  function pauseAll(exceptEl) {
    var vids = document.querySelectorAll('#talks-grid .video-card video');
    for (var i = 0; i < vids.length; i++) {
      var v = vids[i];
      if (!exceptEl || v !== exceptEl) {
        try { v.pause(); } catch (e) {}
        v.removeAttribute('controls');
        var card = v.closest('.video-card');
        if (card) card.classList.remove('is-playing');
      }
    }
  }

  function togglePlay(card) {
    var video = card.querySelector('video');
    if (!video) return;

    if (video.paused) {
      pauseAll(video);
      video.setAttribute('controls', 'controls');
      video.muted = false;
      video.play();
      card.classList.add('is-playing');
    } else {
      video.pause();
      video.removeAttribute('controls');
      card.classList.remove('is-playing');
    }
  }

  document.addEventListener('click', function (e) {
    var card = e.target.closest ? e.target.closest('#talks-grid .video-card') : null;
    if (!card) return;
    togglePlay(card);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var card = document.activeElement && document.activeElement.classList
      && document.activeElement.classList.contains('video-card')
      ? document.activeElement
      : null;
    if (!card) return;
    e.preventDefault();
    togglePlay(card);
  });
})();


(function () {
  const cards = document.querySelectorAll(".video-card");

  function previewPlay(video) {
    if (!video) return;
    video.muted = true;        // hover autoplay requires muted
    video.playsInline = true;
    video.controls = false;    // keep grid clean
    const p = video.play();
    if (p && typeof p.catch === "function") p.catch(() => {});
  }

  function previewStop(video) {
    if (!video) return;
    video.pause();

    // Restore poster reliably (important)
    // load() resets the video element so poster shows again.
    try {
      video.currentTime = 0;
    } catch (e) {}
    video.load();
  }

  async function openFullscreen(video) {
    if (!video) return;

    // Enable controls only in fullscreen
    video.controls = true;
    video.muted = false;

    // Request fullscreen first (some browsers prefer this ordering)
    try {
      if (video.requestFullscreen) {
        await video.requestFullscreen();
      } else if (video.webkitRequestFullscreen) {
        video.webkitRequestFullscreen(); // Safari desktop
      } else if (typeof video.webkitEnterFullscreen === "function") {
        // iOS Safari native fullscreen player
        video.webkitEnterFullscreen();
      }
    } catch (e) {
      // ignore
    }

    // Start playback from a user gesture (this click counts)
    try {
      await video.play();
    } catch (e) {
      // If autoplay with sound is blocked, fall back to muted play
      video.muted = true;
      try { await video.play(); } catch (e2) {}
    }
  }

  function isFullscreen() {
    return !!(document.fullscreenElement || document.webkitFullscreenElement);
  }

  cards.forEach((card) => {
    const video = card.querySelector("video");
    if (!video) return;

    // Ensure posters can display on mobile
    video.setAttribute("playsinline", "");

    // Hover preview (desktop)
    card.addEventListener("mouseenter", () => {
      if (isFullscreen()) return;
      previewPlay(video);
    });

    card.addEventListener("mouseleave", () => {
      if (isFullscreen()) return;
      previewStop(video);
    });

    // Click fullscreen
    card.addEventListener("click", (e) => {
      // If the user clicked a control (in fullscreen), do not hijack
      if (e.target && e.target.tagName && e.target.tagName.toLowerCase() === "video" && isFullscreen()) {
        return;
      }
      openFullscreen(video);
    });
  });

  // When leaving fullscreen: remove controls and restore poster state for grid
  function onExitFullscreen() {
    if (isFullscreen()) return;
    document.querySelectorAll(".video-card video").forEach((v) => {
      v.controls = false;
      v.muted = true;
      previewStop(v);
    });
  }

  document.addEventListener("fullscreenchange", onExitFullscreen);
  document.addEventListener("webkitfullscreenchange", onExitFullscreen);
})();


// hero-reveal.js
(() => {
  const video = document.getElementById("heroVideo");
  const title = document.querySelector(".hero-text .slide-title");
  const subtitle = document.querySelector(".hero-text .slide-sub-title");
  if (!video || !title || !subtitle) return;

  const clamp01 = (x) => Math.min(Math.max(x, 0), 1);

  // Tune these to match your intro.mp4 timing
  const TITLE_START = 0.20, TITLE_END = 0.45;
  const SUB_START   = 0.32, SUB_END   = 0.62;
  const RISE_PX = 18;

  const update = () => {
    const d = video.duration;
    if (!d || !isFinite(d)) return;

    const p = video.currentTime / d;

    const t = clamp01((p - TITLE_START) / (TITLE_END - TITLE_START));
    const s = clamp01((p - SUB_START)   / (SUB_END   - SUB_START));

    title.style.opacity = t.toFixed(3);
    title.style.transform = `translateY(${(RISE_PX * (1 - t)).toFixed(2)}px)`;

    subtitle.style.opacity = s.toFixed(3);
    subtitle.style.transform = `translateY(${(RISE_PX * (1 - s)).toFixed(2)}px)`;
  };

  video.addEventListener("timeupdate", update);
  video.addEventListener("loadedmetadata", update);
  video.addEventListener("play", update);

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) update();
  });
})();

document.addEventListener("DOMContentLoaded", () => {
  const video = document.getElementById("heroVideo");
  const title = document.querySelector(".hero-text .slide-title");
  const subtitle = document.querySelector(".hero-text .slide-sub-title");

  if (!video || !title || !subtitle) {
    console.log("Hero reveal: missing elements", { video: !!video, title: !!title, subtitle: !!subtitle });
    return;
  }

  const clamp01 = (x) => Math.min(Math.max(x, 0), 1);

  const TITLE_START = 0.20, TITLE_END = 0.45;
  const SUB_START = 0.32, SUB_END = 0.62;
  const RISE_PX = 18;

  function render() {
    const d = video.duration;
    if (!d || !isFinite(d) || d <= 0) return;

    const p = video.currentTime / d;

    const t = clamp01((p - TITLE_START) / (TITLE_END - TITLE_START));
    const s = clamp01((p - SUB_START) / (SUB_END - SUB_START));

    title.style.opacity = String(t);
    title.style.transform = `translateY(${RISE_PX * (1 - t)}px)`;

    subtitle.style.opacity = String(s);
    subtitle.style.transform = `translateY(${RISE_PX * (1 - s)}px)`;
  }

  let rafId = null;
  function tick() {
    render();
    rafId = requestAnimationFrame(tick);
  }

  function startRAF() {
    if (rafId == null) tick();
  }
  function stopRAF() {
    if (rafId != null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  }

  video.addEventListener("loadedmetadata", render);
  video.addEventListener("play", startRAF);
  video.addEventListener("pause", stopRAF);
  video.addEventListener("ended", stopRAF);

  render();

  const playAttempt = video.play();
  if (playAttempt && typeof playAttempt.catch === "function") {
    playAttempt.catch((e) => {
      console.log("Hero reveal: autoplay blocked", e);
      title.style.opacity = "1";
      title.style.transform = "translateY(0)";
      subtitle.style.opacity = "1";
      subtitle.style.transform = "translateY(0)";
    });
  }
});

function sampleCurve(curve, t) {
  if (t <= curve[0].t) return curve[0].v;
  if (t >= curve[curve.length - 1].t) return curve[curve.length - 1].v;

  for (let i = 0; i < curve.length - 1; i++) {
    const a = curve[i];
    const b = curve[i + 1];

    if (t >= a.t && t <= b.t) {
      const local = (t - a.t) / (b.t - a.t);
      return a.v + local * (b.v - a.v);
    }
  }
  return 0;
}

document.addEventListener("DOMContentLoaded", function () {
  const video = document.getElementById("heroVideo");
  const heroText = document.querySelector(".hero-text");
  if (!video || !heroText) return;

  const REVEAL_CURVE = [
    { t: 0.1, v: 0 },
    { t: 0.6, v: 0.38 },
    { t: 0.88, v: 0.68 },
    { t: 0.92, v: 0.78 },
    { t: 0.96, v: 0.85 },
    { t: 0.98, v: 0.9 },
    { t: 0.99, v: 0.99 },
    { t: 1, v: 1 }
  ];

  function sampleCurve(curve, t) {
    if (t <= curve[0].t) return curve[0].v;
    if (t >= curve[curve.length - 1].t) return curve[curve.length - 1].v;

    for (let i = 0; i < curve.length - 1; i++) {
      const a = curve[i];
      const b = curve[i + 1];
      if (t >= a.t && t <= b.t) {
        const local = (t - a.t) / (b.t - a.t);
        return a.v + local * (b.v - a.v); // linear interpolation
      }
    }
    return 0;
  }

  // Optional: extra smoothing (low pass). Smaller = smoother but more lag.
  const SMOOTHING = 0.12; // try 0.08 to 0.20
  let displayed = 0;

  let rafId = null;

  function tick() {
    if (video.duration) {
      const p = video.currentTime / video.duration;
      const target = sampleCurve(REVEAL_CURVE, p);

      displayed += (target - displayed) * SMOOTHING;

      heroText.style.setProperty("--wipe", displayed.toFixed(4));
    }
    rafId = requestAnimationFrame(tick);
  }

  function start() {
    if (rafId == null) rafId = requestAnimationFrame(tick);
  }

  function stop() {
    if (rafId != null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  }

  video.addEventListener("play", start);
  video.addEventListener("pause", stop);
  video.addEventListener("ended", stop);
  video.addEventListener("loadedmetadata", function () {
    displayed = 0;
    heroText.style.setProperty("--wipe", "0");
  });

  // Try to autoplay; if blocked, just show text
  video.play().then(start).catch(() => {
    heroText.style.setProperty("--wipe", "1");
  });
});

document.getElementById("mc-form").addEventListener("submit", function (e) {
  e.preventDefault();

  const email = document.getElementById("mc-email").value.trim();
  const msg = document.getElementById("mc-message");

  if (!email) {
    msg.textContent = "Please enter a valid email.";
    return;
  }

  msg.textContent = "Subscribing...";

  const url =
    "https://nyu.us1.list-manage.com/subscribe/post-json" +
    "?u=50a6efae58fa25024df7472c5" +
    "&id=2d7922994b" +
    "&f_id=00507be1f0" +
    "&EMAIL=" + encodeURIComponent(email) +
    "&c=callback";

  const script = document.createElement("script");
  script.src = url;

  window.callback = function (data) {
    if (data.result === "success") {
      msg.textContent = "Thank you. You are subscribed.";
      msg.classList.add("mc-success"); 
      document.getElementById("mc-form").reset();
    } else {
      msg.textContent =
        data.msg?.replace(/<[^>]*>/g, "") ||
        "Subscription failed. Please try again.";
    }
  };

  document.body.appendChild(script);
});
      
      

