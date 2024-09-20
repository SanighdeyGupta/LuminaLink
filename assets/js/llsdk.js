(function () {
  // Utility functions
  function getBrowser() {
    const userAgent = navigator.userAgent;
    if (/Chrome/.test(userAgent)) return "Chrome";
    if (/Firefox/.test(userAgent)) return "Firefox";
    if (/Safari/.test(userAgent) && !/Chrome/.test(userAgent)) return "Safari";
    if (/Edge/.test(userAgent)) return "Edge";
    return "Other";
  }

  function getOSType() {
    const platform = navigator.platform;
    if (/Win/.test(platform)) return "Windows";
    if (/Mac/.test(platform)) return "MacOS";
    if (/Linux/.test(platform)) return "Linux";
    if (/iPhone|iPad|iPod/.test(platform)) return "iOS";
    if (/Android/.test(platform)) return "Android";
    return "Other";
  }

  function getTrafficSource() {
    const referrer = document.referrer;
    if (!referrer) return "Direct Traffic";
    const searchEngines = ["google", "bing", "yahoo", "baidu", "duckduckgo"];
    const socialMedia = ["facebook", "twitter", "linkedin", "instagram", "youtube"];
    if (searchEngines.some((engine) => referrer.includes(engine))) return "Search Engine";
    if (socialMedia.some((media) => referrer.includes(media))) return "Social Media";
    return "Other";
  }

  function getCurrentCountry(callback) {
    $.getJSON("https://ipapi.co/json/", function (data) {
      callback(data.country_name);
    }).fail(function () {
      callback("Unknown");
    });
  }

  function isFirstTimeVisitor() {
    return localStorage.getItem("firstTimeVisitor") === null;
  }

  function isReturningVisitor() {
    return localStorage.getItem("firstTimeVisitor") !== null;
  }

  function updateFirstTimeVisitor() {
    if (!localStorage.getItem("firstTimeVisitor")) {
      localStorage.setItem("firstTimeVisitor", "false");
    }
  }

  function sendAnalyticsData(scriptHost, placementId, eventType, country) {
    const eventData = {
      browser: getBrowser(),
      os: getOSType(),
      referrer: getTrafficSource(),
      country: country,
      firstTimeVisitor: isFirstTimeVisitor(),
      returningVisitor: isReturningVisitor(),
    };

    fetch(`${scriptHost}/track-event/${placementId}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ event: eventType, eventData: eventData }),
    }).catch((err) => console.error("Failed to send analytics data:", err));
  }

  // Fetch placement data and render content if conditions match
  function initializeSDK(dataId) {
    const script = document.querySelector(`script[data-llplacement-id="${dataId}"]`);
    const scriptHost = new URL(script.src).origin;

    fetch(`${scriptHost}/get-placement-data/${dataId}/`)
      .then((response) => response.json())
      .then((data) => {
        const currentPageUrl = window.location.href;
        if (currentPageUrl === data.page_url) {
          getCurrentCountry((country) => {
            sendAnalyticsData(scriptHost, dataId, "view", country);
            const placementData = JSON.parse(data.data);
            placementData.forEach((placement) => {
              const conditions = placement.conditions;
              conditions.forEach((condition) => {
                const shouldRender = evaluateCondition(condition, country);
                if (shouldRender) {
                  const element = document.querySelector(placement.selector);
                  if (element) {
                    element.innerHTML = condition.htmlContent;

                    element.addEventListener("click", () => {
                      sendAnalyticsData(scriptHost, dataId, "click", country);
                    });
                  }
                }
              });
            });
          });
        }
      });
  }

  function evaluateCondition(condition, country) {
    switch (condition.param) {
      case "Browser":
        return condition.condition === "equals" && condition.value === getBrowser();
      case "OS":
        return condition.condition === "equals" && condition.value === getOSType();
      case "Traffic Source":
        return condition.condition === "equals" && condition.value === getTrafficSource();
      case "Country":
        return condition.condition === "equals" && condition.value === country;
      case "First Time Visitor":
        return condition.condition === "equals" && condition.value === isFirstTimeVisitor().toString();
      case "Returning Visitor":
        return condition.condition === "equals" && condition.value === isReturningVisitor().toString();
      default:
        return false;
    }
  }

  // Initialization
  document.addEventListener("DOMContentLoaded", () => {
    const scriptElement = document.querySelector("script[data-llplacement-id]");
    const dataId = scriptElement.getAttribute("data-llplacement-id");
    if (window.self !== window.top) {
      console.log("Running inside an iframe");
    } else {
      initializeSDK(dataId);
      updateFirstTimeVisitor();
    }
  });
})();
