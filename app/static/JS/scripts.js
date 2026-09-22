const tagsDiv = document.getElementById('ingredients-tags');
let currentIngredients = JSON.parse(tagsDiv ? (tagsDiv.dataset.ingredients || '[]') : '[]');

let allFetchedRecipes = [];
let currentJournalMeals = [];
let currentJournalTitles = [];
let nextSuggestionsOffset = 0;
let hasMoreSuggestions = false;
let suggestionsAbortController = null;
let isLoadingMore = false;

/* ------------------------------ Affichage des badges frigo ------------------------------ */
function renderTags() {
    if (!tagsDiv) return;
    tagsDiv.dataset.ingredients = JSON.stringify(currentIngredients);

    if (currentIngredients.length === 0) {
        tagsDiv.innerHTML = `<p class="fridge-empty">Ton frigo est vide pour l'instant.</p>`;
        return;
    }

    tagsDiv.innerHTML = currentIngredients.map(item => {
        const escaped = item.replace(/'/g, "\\'");
        const formattedItem = item.charAt(0).toUpperCase() + item.slice(1);

        return `<span class="ingredient-tag">
            ${formattedItem}
            <button type="button"
                    onclick="removeIngredient('${escaped}')"
                    class="ingredient-remove">×</button>
        </span>`;
    }).join('');
}

async function quickAdd(ingredient) {
    if (currentIngredients.some(item => item.toLowerCase() === ingredient.toLowerCase())) {
        return;
    }

    const inputField = document.getElementById('ingredients-input');
    if (inputField) inputField.value = ingredient;
    await submitFridgeUpdate([ingredient]);
}

async function removeIngredient(item) {
    const previousIngredients = [...currentIngredients];

    currentIngredients = currentIngredients.filter(
        ingredient => ingredient.toLowerCase() !== item.toLowerCase()
    );
    renderTags();

    try {
        const res = await fetch(`/fridge/${encodeURIComponent(item)}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (!res.ok) {
            throw new Error("Impossible de supprimer l'ingrédient.");
        }

        const data = await res.json().catch(() => ({}));
        currentIngredients = data.ingredients || currentIngredients;
        renderTags();

        await loadRecipeSuggestions(true);
    } catch (err) {
        currentIngredients = previousIngredients;
        renderTags();
        console.error("Erreur lors de la suppression :", err);
    }
}

async function submitFridgeUpdate(newItemsList = null) {
    const statusText = document.getElementById('fridge-status');
    const inputField = document.getElementById('ingredients-input');

    let newItems = newItemsList;

    if (!newItems && inputField) {
        const rawInput = inputField.value;
        const normalizedInput = rawInput
            .replace(/œ/g, 'oe')
            .replace(/Œ/g, 'Oe');

        newItems = normalizedInput
            .split(',')
            .map(item => item.trim().toLowerCase())
            .filter(Boolean);
    }

    if (!newItems || newItems.length === 0) {
        return;
    }

    const updatedIngredients = Array.from(
        new Set([...currentIngredients, ...newItems])
    );

    if (statusText) {
        statusText.textContent = "Sauvegarde en cours...";
        statusText.className = "fridge-status fridge-status-loading";
        statusText.classList.remove('hidden');
    }

    try {
        const res = await fetch('/fridge', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ ingredients: updatedIngredients })
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
            throw new Error(data.detail || "Erreur de sauvegarde");
        }

        currentIngredients = data.ingredients || updatedIngredients;

        if (statusText) {
            statusText.textContent = "Contenu du frigo sauvegardé !";
            statusText.className = "fridge-status fridge-status-success";
        }

        if (inputField) inputField.value = '';
        renderTags();

        loadRecipeSuggestions(true);
    } catch (err) {
        if (statusText) {
            statusText.textContent = err.message || "Impossible de sauvegarder.";
            statusText.className = "fridge-status fridge-status-error";
        }
    }
}

/* ------------------------------ Chargement du Journal (3 Plats) ------------------------------ */
async function loadJournalData() {
    try {
        const res = await fetch('/journal');
        if (!res.ok) return;

        const data = await res.json();
        currentJournalMeals = data.meals || [];
        currentJournalTitles = currentJournalMeals.map(m => (m.title || "").toLowerCase());

        // Mise à jour des barres de progression
        updateProgressBar('calories', data.totals.calories, data.percentages.calories, 'kcal');
        updateProgressBar('protein', data.totals.protein_g, data.percentages.protein_g, 'g');
        updateProgressBar('carbs', data.totals.carbs_g, data.percentages.carbs_g, 'g');
        updateProgressBar('fat', data.totals.fat_g, data.percentages.fat_g, 'g');

        // Check si tous les objectifs sont atteints (100% ou plus sur Calories + Protéines)
        const banner = document.getElementById('goal-reached-banner');
        if (banner) {
            const p = data.percentages || {};
            const isGoalReached = (p.calories >= 100) && (p.protein_g >= 100);

            if (isGoalReached) {
                banner.classList.remove('hidden');
            } else {
                banner.classList.add('hidden');
            }
        }

        // Affichage des 3 emplacements de plats
        const mealsContainer = document.getElementById('journal-meals-list');
        if (mealsContainer) {
            const slots = ['Plat 1', 'Plat 2', 'Plat 3'];

            mealsContainer.innerHTML = slots.map((label, index) => {
                const meal = currentJournalMeals[index];

                if (meal) {
                    return `
                        <div class="p-3 rounded-xl border border-emerald-200 bg-emerald-50/40 flex flex-col justify-between">
                            <div>
                                <div class="flex justify-between items-center mb-1">
                                    <span class="text-xs font-bold text-emerald-700 uppercase">${label}</span>
                                    <button type="button" onclick="deleteFromJournal(${meal.id})" class="text-red-500 hover:text-red-700 font-bold text-base transition px-1" title="Retirer ce plat">
                                        ×
                                    </button>
                                </div>
                                <h4 class="font-bold text-gray-800 text-sm line-clamp-1">${meal.title}</h4>
                            </div>
                            <div class="text-xs text-gray-600 mt-2 font-medium">
                                🔥 ${meal.calories} kcal | 💪 ${meal.protein_g}g P
                            </div>
                        </div>
                    `;
                }

                return `
                    <div class="p-3 rounded-xl border border-dashed border-gray-200 bg-gray-50/50 flex flex-col items-center justify-center text-center text-gray-400 text-xs">
                        <span class="font-semibold text-gray-500 uppercase text-[10px]">${label}</span>
                        <span class="italic text-[11px] mt-1">Vide</span>
                    </div>
                `;
            }).join('');
        }

        renderRecipeGrid();

    } catch (err) {
        console.error("Erreur chargement journal :", err);
    }
}

function updateProgressBar(key, currentVal, percentage, unit) {
    const bar = document.getElementById(`bar-${key}`);
    const label = document.getElementById(`label-${key}`);
    if (!bar || !label) return;

    bar.style.width = `${Math.min(100, percentage)}%`;
    label.innerText = `${currentVal} ${unit} (${percentage}%)`;

    if (percentage >= 100) {
        bar.className = "bg-red-500 h-full transition-all duration-500";
    } else {
        const colors = { calories: 'bg-blue-500', protein: 'bg-emerald-500', carbs: 'bg-amber-500', fat: 'bg-purple-500' };
        bar.className = `${colors[key]} h-full transition-all duration-500`;
    }
}

async function addToJournal(title, calories, protein, carbs, fat) {
    if (currentJournalMeals.length >= 3) {
        alert("Tu as déjà sélectionné tes 3 plats pour aujourd'hui ! Supprime un plat pour en ajouter un autre.");
        return;
    }

    const nextSlotKey = `slot_${currentJournalMeals.length + 1}`;

    try {
        const res = await fetch('/journal/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                meal_type: nextSlotKey,
                title: title,
                calories: Math.round(calories),
                protein_g: Math.round(protein * 10) / 10,
                carbs_g: Math.round(carbs * 10) / 10,
                fat_g: Math.round(fat * 10) / 10
            })
        });

        if (res.ok) {
            await loadJournalData();
        }
    } catch (err) {
        console.error("Erreur d'ajout au journal :", err);
    }
}

async function deleteFromJournal(entryId) {
    try {
        const res = await fetch(`/journal/${entryId}`, { method: 'DELETE' });
        if (res.ok) {
            await loadJournalData();
        }
    } catch (err) {
        console.error("Erreur de suppression :", err);
    }
}

async function resetDay() {
    try {
        const res = await fetch('/journal/reset', { method: 'POST' });
        if (res.ok) {
            await loadJournalData();
        }
    } catch (err) {
        console.error("Erreur réinitialisation :", err);
    }
}

/* ------------------------------ Formulaire Frigo ------------------------------ */
const fridgeForm = document.getElementById('fridge-form');
if (fridgeForm) {
    fridgeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await submitFridgeUpdate();
    });
}

/* ------------------------------ Suggestions de Recettes ------------------------------ */
async function loadRecipeSuggestions(reset = true) {
    const container = document.getElementById('recipes-container');
    const loadMoreBtn = document.getElementById('load-more-btn');

    if (!container || isLoadingMore) {
        return;
    }

    if (!currentIngredients || currentIngredients.length === 0) {
        allFetchedRecipes = [];
        nextSuggestionsOffset = 0;
        hasMoreSuggestions = false;

        container.innerHTML = `<p class="text-gray-500 text-sm italic col-span-3">Ajoute des ingrédients dans ton frigo pour générer des recettes adaptées.</p>`;
        if (loadMoreBtn) loadMoreBtn.classList.add('hidden');
        return;
    }

    if (reset) {
        if (suggestionsAbortController) {
            suggestionsAbortController.abort();
        }

        suggestionsAbortController = new AbortController();
        allFetchedRecipes = [];
        nextSuggestionsOffset = 0;
        hasMoreSuggestions = false;

        container.innerHTML = `<p class="text-gray-500 text-sm italic col-span-3">Chargement des suggestions en cours...</p>`;
    } else {
        isLoadingMore = true;
        if (loadMoreBtn) {
            loadMoreBtn.disabled = true;
            loadMoreBtn.textContent = "Chargement...";
        }
    }

    try {
        const params = new URLSearchParams({
            offset: String(nextSuggestionsOffset),
            limit: '3'
        });

        const res = await fetch(`/suggestions/?${params.toString()}`, {
            credentials: 'include',
            signal: reset ? suggestionsAbortController.signal : undefined
        });

        if (!res.ok) {
            throw new Error(`Erreur serveur HTTP ${res.status}`);
        }

        const data = await res.json();
        const newRecipes = data.recipes || [];

        if (reset) {
            allFetchedRecipes = newRecipes;
        } else {
            allFetchedRecipes = [...allFetchedRecipes, ...newRecipes];
        }

        nextSuggestionsOffset += newRecipes.length;
        hasMoreSuggestions = Boolean(data.has_more);

        if (allFetchedRecipes.length === 0) {
            container.innerHTML = `<p class="text-gray-500 text-sm italic col-span-3">Aucune recette trouvée avec ces ingrédients. Essaie d'en ajouter d'autres !</p>`;
        } else {
            renderRecipeGrid();
        }

        if (loadMoreBtn) loadMoreBtn.classList.toggle('hidden', !hasMoreSuggestions);
    } catch (err) {
        if (err.name === 'AbortError') {
            return;
        }

        console.error("Erreur suggestions:", err);

        if (reset) {
            container.innerHTML = `<p class="text-red-500 text-sm col-span-3">Impossible de charger les suggestions de recettes.</p>`;
        }
    } finally {
        isLoadingMore = false;
        if (loadMoreBtn) {
            loadMoreBtn.disabled = false;

            if (hasMoreSuggestions) {
                loadMoreBtn.textContent = "Voir plus de suggestions ↓";
            }
        }
    }
}

function renderRecipeGrid() {
    const container = document.getElementById('recipes-container');
    if (!container) return;

    const isJournalFull = currentJournalMeals.length >= 3;

    container.innerHTML = allFetchedRecipes.map((item, index) => {
        const recipe = item.recipe;
        const nutrients = item.nutrients || {};
        const rawTitle = recipe.title || 'Recette';

        const isAdded = currentJournalTitles.includes(rawTitle.toLowerCase());

        return `
            <div class="border border-gray-200 rounded-xl overflow-hidden shadow-sm flex flex-col justify-between transition-all duration-300 ${isAdded ? 'bg-gray-50 opacity-60' : 'bg-white'}">
                <div>
                    <img
                        src="${recipe.thumbnail || ''}"
                        alt="${rawTitle}"
                        class="h-36 w-full object-cover"
                    >
                    <div class="p-3">
                        <h3 class="font-bold text-sm text-gray-800 line-clamp-1">
                            ${rawTitle}
                        </h3>
                        <div class="flex gap-2 text-xs text-gray-600 mt-2">
                            <span class="bg-amber-50 text-amber-700 px-2 py-0.5 rounded font-medium">
                                🔥 ${Math.round(nutrients.calories || 0)} kcal
                            </span>
                            <span class="bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-medium">
                                💪 ${Math.round(nutrients.protein_g || 0)}g prot
                            </span>
                        </div>
                    </div>
                </div>

                <div class="p-3 pt-0 space-y-2">
                    ${isAdded 
                        ? `<button type="button" disabled class="w-full bg-gray-200 text-gray-500 font-bold py-1.5 px-2 rounded-lg text-xs cursor-not-allowed">✓ Ajouté</button>`
                        : isJournalFull
                        ? `<button type="button" disabled class="w-full bg-gray-100 text-gray-400 font-bold py-1.5 px-2 rounded-lg text-xs cursor-not-allowed">3 plats sélectionnés</button>`
                        : `
                            <button 
                                type="button"
                                data-index="${index}"
                                class="add-to-journal-btn w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-1.5 px-3 rounded-lg text-xs transition">
                                 Ajouter à ma journée
                            </button>
                        `
                    }

                    <a
                        href="/recipe/${encodeURIComponent(recipe.id)}"
                        class="block text-center w-full py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-semibold rounded-lg transition"
                    >
                        Voir la recette
                    </a>
                </div>
            </div>
        `;
    }).join('');

    // Attache proprement l'événement de clic à tous les boutons ajoutés
    document.querySelectorAll('.add-to-journal-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = e.currentTarget.getAttribute('data-index');
            const item = allFetchedRecipes[index];
            if (!item) return;

            const recipe = item.recipe;
            const nutrients = item.nutrients || {};

            addToJournal(
                recipe.title || 'Recette',
                nutrients.calories || 0,
                nutrients.protein_g || 0,
                nutrients.carbs_g || 0,
                nutrients.fat_g || 0
            );
        });
    });
}

/* ------------------------------ Initialisation ------------------------------ */
const loadMoreBtn = document.getElementById('load-more-btn');
if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', () => {
        loadRecipeSuggestions(false);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    renderTags();
    loadRecipeSuggestions(true);
    loadJournalData();
});