document.addEventListener('DOMContentLoaded', function() {
    const car1Select = document.getElementById('car1Select');
    const car2Select = document.getElementById('car2Select');
    const car1Details = document.getElementById('car1Details');
    const car2Details = document.getElementById('car2Details');

    let cars = [];
    let selectedCar1 = null;
    let selectedCar2 = null;

    // Fetch all cars for the dropdowns
    fetch('/api/cars/')
        .then(response => response.json())
        .then(data => {
            cars = data;
            populateDropdowns();
        })
        .catch(error => console.error('Error loading cars:', error));

    function populateDropdowns() {
        cars.forEach(car => {
            car1Select.innerHTML += `<option value="${car.id}">${car.title} - €${car.price.toLocaleString()}</option>`;
            car2Select.innerHTML += `<option value="${car.id}">${car.title} - €${car.price.toLocaleString()}</option>`;
        });
    }

    function updateCarDetails(carData, container) {
        if (!carData) {
            container.style.opacity = '0';
            return;
        }

        const elements = {
            image: container.querySelector('.car-image'),
            title: container.querySelector('.car-title'),
            price: container.querySelector('.car-price'),
            year: container.querySelector('.year'),
            km: container.querySelector('.km'),
            fuel: container.querySelector('.fuel'),
            transmission: container.querySelector('.transmission')
        };

        // Update with animation
        container.style.opacity = '0';
        setTimeout(() => {
            elements.image.src = carData.image || '/static/img/no-image.svg';
            elements.image.alt = carData.title;
            elements.title.textContent = carData.title;
            elements.price.textContent = `€ ${carData.price.toLocaleString()}`;
            elements.year.textContent = carData.year;
            elements.km.textContent = carData.km.toLocaleString();
            elements.fuel.textContent = carData.fuel_type;
            elements.transmission.textContent = carData.transmission;
            container.style.opacity = '1';
        }, 300);
    }

    function updateComparisonIndicators() {
        if (!selectedCar1 || !selectedCar2) return;

        const indicators = {
            price: document.querySelector('[data-type="price"] .arrow-container'),
            year: document.querySelector('[data-type="year"] .arrow-container'),
            km: document.querySelector('[data-type="km"] .arrow-container')
        };

        // Compare price
        updateIndicator(indicators.price, selectedCar1.price, selectedCar2.price, false);
        // Compare year (higher is better)
        updateIndicator(indicators.year, selectedCar1.year, selectedCar2.year, true);
        // Compare km (lower is better)
        updateIndicator(indicators.km, selectedCar1.km, selectedCar2.km, false);

        // Update value highlighting
        updateValueHighlighting('price', selectedCar1.price, selectedCar2.price, false);
        updateValueHighlighting('year', selectedCar1.year, selectedCar2.year, true);
        updateValueHighlighting('km', selectedCar1.km, selectedCar2.km, false);
    }

    function updateIndicator(container, value1, value2, higherIsBetter) {
        const arrows = {
            left: container.querySelector('.fa-arrow-left'),
            equals: container.querySelector('.fa-equals'),
            right: container.querySelector('.fa-arrow-right')
        };

        Object.values(arrows).forEach(arrow => arrow.classList.add('hidden'));

        if (value1 === value2) {
            arrows.equals.classList.remove('hidden');
        } else if ((value1 > value2) === higherIsBetter) {
            arrows.left.classList.remove('hidden');
        } else {
            arrows.right.classList.remove('hidden');
        }
    }

    function updateValueHighlighting(type, value1, value2, higherIsBetter) {
        const value1Element = car1Details.querySelector(`.${type}`);
        const value2Element = car2Details.querySelector(`.${type}`);

        value1Element.classList.remove('highlight-better', 'highlight-worse');
        value2Element.classList.remove('highlight-better', 'highlight-worse');

        if (value1 === value2) return;

        if ((value1 > value2) === higherIsBetter) {
            value1Element.classList.add('highlight-better');
            value2Element.classList.add('highlight-worse');
        } else {
            value1Element.classList.add('highlight-worse');
            value2Element.classList.add('highlight-better');
        }
    }

    // Event listeners for dropdowns
    car1Select.addEventListener('change', function() {
        const carId = this.value;
        selectedCar1 = cars.find(car => car.id === parseInt(carId));
        updateCarDetails(selectedCar1, car1Details);
        updateComparisonIndicators();
    });

    car2Select.addEventListener('change', function() {
        const carId = this.value;
        selectedCar2 = cars.find(car => car.id === parseInt(carId));
        updateCarDetails(selectedCar2, car2Details);
        updateComparisonIndicators();
    });
});
