document.addEventListener('DOMContentLoaded', () => {
    const addExamBtn = document.getElementById('generatePlanBtn');
    const planContainer = document.getElementById('planContainer');
    const modal = document.getElementById('examModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const examForm = document.getElementById('examForm');
    const submitBtn = document.querySelector('.form-submit-btn'); // The submit button

    let isSubmitting = false;

    // Modal Logic (no changes)
    function openModal() { modal.classList.add('show'); }
    function closeModal() { modal.classList.remove('show'); }
    addExamBtn.addEventListener('click', openModal);
    closeModalBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (event) => { if (event.target === modal) closeModal(); });

    // --- NEW: Listening to BUTTON CLICK, not FORM SUBMIT ---
    submitBtn.addEventListener('click', async (event) => {
        event.preventDefault(); // Still important to prevent default button actions
        console.log("--- SUBMIT BUTTON CLICKED ---");

        if (isSubmitting) {
            console.log("Guard flag is TRUE. Halting execution.");
            return;
        }
        
        console.log("Guard flag is FALSE. Proceeding.");
        isSubmitting = true;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Hazırlanıyor...';

        planContainer.innerHTML = '<div class="loading"><h2>AI Koçunuz yeni sonuçlarınıza göre en iyi planı hazırlıyor...</h2></div>';
        closeModal();
        
        const formData = new FormData(examForm);
        const newExamResults = {};
        for (const [key, value] of formData.entries()) {
            if (value) {
                newExamResults[key] = parseFloat(value);
            }
        }
        
        if (Object.keys(newExamResults).length === 0) {
            planContainer.innerHTML = '<div class="error"><h2>Lütfen en az bir sınav sonucu girin.</h2></div>';
            isSubmitting = false;
            submitBtn.disabled = false;
            submitBtn.textContent = 'Planımı Güncelle';
            return;
        }

        try {
            console.log("Sending FETCH POST request now...");
            const response = await fetch('http://127.0.0.1:5001/generate-plan-with-new-results', {
                method: 'POST', // Explicitly POST
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newExamResults),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
            }

            const planData = await response.json();
            displayPlan(planData);

        } catch (error) {
            console.error("Error fetching study plan:", error);
            planContainer.innerHTML = `<div class="error"><h2>Bir hata oluştu: ${error.message}</h2></div>`;
        } finally {
            console.log("FINALLY block reached. Resetting guard flag.");
            isSubmitting = false;
            submitBtn.disabled = false;
            submitBtn.textContent = 'Planımı Güncelle';
        }
    });

    function displayPlan(data) {
        // ... this function is correct and does not need to be changed ...
        console.log("RAW DATA RECEIVED FROM AI:", JSON.stringify(data, null, 2));
        const welcomeMessageElement = document.querySelector('.welcome-message p');
        planContainer.innerHTML = '';

        if (!data || !data.plan || !Array.isArray(data.plan)) {
            console.error("Invalid data structure.", data);
            planContainer.innerHTML = '<div class="error"><h2>AI geçersiz bir plan formatı gönderdi.</h2></div>';
            return;
        }
        
        if (welcomeMessageElement && data.weekly_summary) {
            welcomeMessageElement.textContent = data.weekly_summary;
        }
        
        data.plan.forEach(day => {
            let tasksHtml = day.tasks.map(task => `
                <li>
                    <div class="task-subject">${task.subject || 'Görev'}</div>
                    <p class="task-activity">${task.activity || 'Açıklama yok.'}</p>
                </li>
            `).join('');

            if (tasksHtml.length === 0) {
                tasksHtml = '<li><p class="task-activity">Bugün için görev yok.</p></li>';
            }
            
            const dayCardHtml = `<div class="day-card"><h3>${day.day}</h3><ul>${tasksHtml}</ul></div>`;
            planContainer.insertAdjacentHTML('beforeend', dayCardHtml);
        });
    }
});