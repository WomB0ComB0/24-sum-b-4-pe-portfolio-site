(async () => {
  try {
    const res = await fetch("http://127.0.0.1:5000/api/v1/hobbies", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "mlh",
      },
    });

    if (res.status !== 200) {
      console.log(`Status: ${res.status}, Body: ${JSON.stringify(res.body, null, 2)}`);
      return;
    }

    const data = await res.json();
    console.log(data);
    return data;
  } catch (error) {
    console.error("Bad response:", error);
    throw new Error("Bad response");
  }
})();