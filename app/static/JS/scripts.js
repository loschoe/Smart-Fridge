const tagsDiv = document.getElementById('ingredients-tags');
let currentIngredients = JSON.parse(tagsDiv.dataset.ingredients || '[]');

let allFetchedRecipes = [];
let nextSuggestionsOffset = 0;
let hasMoreSuggestions = false;
let suggestionsAbortController = null;
let isLoadingMore = false;

function renderTags() {
    tagsDiv.dataset.ingredients = JSON.stringify(currentIngredients);

    if (currentIngredients.length === 0) {
        tagsDiv.innerHTML = `<p class="fridge-empty">Ton frigo est vide pour l'instant.</p>`;
        return;
    }

    tagsDiv.innerHTML = currentIngredients.map(item => {
        const escaped = item.replace(/'/g, "\\'");
        // Formate la première lettre en majuscule
        const formattedItem = item.charAt(0).toUpperCase() + item.slice(1);

        return `<span class="ingredient-tag">
            ${item}
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

    document.getElementById('ingredients-input').value = ingredient;
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

    if (!newItems) {
        const rawInput = inputField.value;
        const normalizedInput = rawInput
            .replace(/œ/g, 'oe')
            .replace(/Œ/g, 'Oe');

        newItems = normalizedInput
            .split(',')
            .map(item => item.trim().toLowerCase())
            .filter(Boolean);
    }

    if (newItems.length === 0) {
        return;
    }

    const updatedIngredients = Array.from(
        new Set([...currentIngredients, ...newItems])
    );

    statusText.textContent = "Sauvegarde en cours...";
    statusText.className = "fridge-status fridge-status-loading";
    statusText.classList.remove('hidden');

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

        statusText.textContent = "Contenu du frigo sauvegardé !";
        statusText.className = "fridge-status fridge-status-success";

        inputField.value = '';
        renderTags();

        // Le frigo est déjà enregistré. Le recalcul des recettes est déclenché
        // ensuite et n'empêche plus la sauvegarde d'être interactive.
        loadRecipeSuggestions(true);
    } catch (err) {
        statusText.textContent = err.message || "Impossible de sauvegarder.";
        statusText.className = "fridge-status fridge-status-error";
    }
}

document.getElementById('fridge-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await submitFridgeUpdate();
});

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
        loadMoreBtn.classList.add('hidden');
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
        loadMoreBtn.disabled = true;
        loadMoreBtn.textContent = "Chargement...";
    }

    try {
        const params = new URLSearchParams({
            offset: String(nextSuggestionsOffset),
            limit: '3'
        });

        const res = await fetch(`/suggestions/?${params.toString()}`, {
            credentials: 'include',
            signal: reset
                ? suggestionsAbortController.signal
                : undefined
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

        loadMoreBtn.classList.toggle('hidden', !hasMoreSuggestions);
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
        loadMoreBtn.disabled = false;

        if (hasMoreSuggestions) {
            loadMoreBtn.textContent = "Voir plus de suggestions ↓";
        }
    }
}

function renderRecipeGrid() {
    const container = document.getElementById('recipes-container');

    container.innerHTML = allFetchedRecipes.map(item => {
        const recipe = item.recipe;
        const nutrients = item.nutrients || {};

        return `
            <div class="border border-gray-200 rounded-xl overflow-hidden bg-white shadow-sm flex flex-col">
                <img
                    src="${recipe.thumbnail || ''}"
                    alt="${recipe.title || 'Recette'}"
                    class="h-36 w-full object-cover"
                >
                <div class="p-3 flex-1 flex flex-col justify-between">
                    <div>
                        <h3 class="font-bold text-sm text-gray-800 line-clamp-1">
                            ${recipe.title || 'Recette'}
                        </h3>
                        <div class="flex gap-2 text-xs text-gray-600 mt-2">
                            <span class="bg-amber-50 text-amber-700 px-2 py-0.5 rounded font-medium">
                                🔥 ${Math.round(nutrients.calories || 0)} kcal
                            </span>
                            <span class="bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-medium">
                                🥩 ${Math.round(nutrients.protein_g || 0)}g p
                            </span>
                        </div>
                    </div>

                    <a
                        href="/recipe/${encodeURIComponent(recipe.id)}"
                        class="mt-3 block text-center w-full py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg transition"
                    >
                        Voir la recette complète
                    </a>
                </div>
            </div>
        `;
    }).join('');
}

document.getElementById('load-more-btn').addEventListener('click', () => {
    loadRecipeSuggestions(false);
});

document.addEventListener('DOMContentLoaded', () => {
    loadRecipeSuggestions(true);
});