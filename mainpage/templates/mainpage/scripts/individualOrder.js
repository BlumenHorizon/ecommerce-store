document.addEventListener("DOMContentLoaded", function () {
    const individualOrderForm = document.getElementById('individual-order-form');
    const captchaInput = document.getElementById('id_captcha');
    const siteKey = captchaInput.dataset.siteKey;

    async function sendAjax(form) {
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form)
            });

            const data = await response.json();

            if (data.status === "success") {
                showToast(data.detail, "success");
                disableForm(form);
            } else {
                let errors = JSON.parse(data.errors);
                let errorsText = Object.entries(errors)
                    .map(([field, errors]) => {
                        return errors.map(error => `${error.message}`).join('\n');
                    })
                    .join('\n');

                showToast(`${data.detail}\n${errorsText}`, "danger");
            }
        } catch (error) {
            console.log(error);
            showToast(gettext("Произошла ошибка. Повторите попытку позже."), "danger");
        }
    }

    individualOrderForm.addEventListener('submit', function (e) {
        e.preventDefault();

        grecaptcha.ready(function () {
            grecaptcha.execute(siteKey).then(function (token) {
                captchaInput.value = token;
                sendAjax(individualOrderForm);
            });
        });
    });
});