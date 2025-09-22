Module 2 of the Engineering Physics course (BAPHY105) is titled "Mathematical Foundations of Quantum Mechanics" and is allocated 10 hours of lecture time. This module focuses on the mathematical tools necessary for understanding quantum mechanics.
Here are the key topics covered in Module 2:
• Introduction to Linear Vector Space
    ◦ A linear vector space, in an abstract sense, is a set of objects that can be combined like vectors.
    ◦ It consists of two sets of elements: a set of vectors (e.g., φ, ψ, χ) and a set of scalars (e.g., a, b, c).
    ◦ There is no inherent basis (set of axes) in an abstract vector space; the vectors themselves are the fundamental objects.
    ◦ The state space of a quantum system is described as a vector space, specifically over the complex field (ℂ).
    ◦ Key properties (axioms) for vectors in a linear vector space include:
        ▪ Addition:
            • Commutativity: φ + ψ = ψ + φ.
            • Associativity: (φ + ψ) + χ = φ + (ψ + χ).
            • Existence of a Zero Vector (Origin): For any vector φ, there exists a unique zero vector (0) such that φ + 0 = φ.
            • Existence of a Symmetric (Inverse) Vector: For every vector φ, there corresponds a unique vector -φ such that φ + (-φ) = 0.
        ▪ Scalar Multiplication:
            • The product of a scalar with a vector is another vector.
            • Associativity with Scalars: (a b)φ = a(b φ).
            • Distributivity over Vector Addition: a(φ + ψ) = aφ + aψ.
            • Distributivity over Scalar Addition: (a + b)φ = aφ + bφ.
            • For every vector φ, there must exist a unitary scalar (I) such that Iφ = φ, and a zero scalar (0) such that 0φ = 0.
    ◦ A vector subspace is a non-empty subset that satisfies all vector space axioms.
• Basis Vectors
    ◦ A spanning set for a vector space of dimension 'n' is a set of 'n' vectors such that any vector in that space can be expressed as a linear combination of these basis vectors.
    ◦ In three-dimensional space, a vector can be represented as a linear combination of mutually perpendicular unit vectors, which form an orthonormal basis.
    ◦ The dimension of a space is defined as the maximum number of mutually orthogonal vectors it contains. A basis always exists.
• Orthonormal Sets
    ◦ A set of vectors is orthonormal if their inner product (or scalar product) is 0 if they are different vectors, and 1 if they are the same vector (i.e., (aᵢ, aⱼ) = δᵢⱼ, where δᵢⱼ is the Kronecker delta).
• Hilbert Space
    ◦ A Hilbert space (H) is a linear space (vector space) in which the scalars are complex numbers and it features a defined inner product operation (• : H × H → C).
    ◦ The mathematical properties and structure of Hilbert spaces are essential for a proper understanding of the formalism of quantum mechanics.
    ◦ Key properties of the inner product in a Hilbert space include:
        ▪ x • y = (y • x)* (where * denotes the complex conjugate).
        ▪ x • x ≥ 0.
        ▪ x • x = 0 if and only if x = 0.
        ▪ x • y is linear under scalar multiplication and vector addition in both x and y.
    ◦ A Hilbert space is also separable and complete, meaning every Cauchy sequence in the space converges to an element within the space.
• Representation of Quantum States using Dirac Notation
    ◦ Dirac notation is used to represent vectors in quantum mechanics, often called ket vectors (e.g., |v⟩).
    ◦ The inner product (⟨x|y⟩) is equivalent to the matrix product of a conjugated row vector (the "bra" ⟨x|) and a normal column vector (the "ket" |y⟩).
    ◦ The "bra" ⟨s| is defined as the conjugate transpose (adjoint) of the "ket" |s⟩, denoted as |s⟩†.
• Inner and Outer Products
    ◦ The inner product (also called scalar product or dot product) of two vectors a and b in a complex n-dimensional space is defined as (a,b) = Σ aᵢ* bᵢ. It is a complex number.
    ◦ The inner product of a vector with itself, (a,a) = Σ |aᵢ|², represents the norm squared and is a real number.
    ◦ The term "outer product" is listed in the syllabus but not explicitly elaborated upon in the provided sources.
• Tensor Product of Vector Spaces
    ◦ This topic is listed in the syllabus but no detailed information regarding it is provided in the given sources.
• Linear Operators
    ◦ Quantum mechanical problems involve linear operators, along with matrix algebra and Dirac notation.
    ◦ Specific types of operators covered include Hermitian, Unitary, and Projection operators. However, the sources do not provide further definitions or details on these specific operators.
• Matrix Algebra
    ◦ Matrix algebra is a fundamental tool for understanding quantum mechanical problems, particularly those involving linear operators. The sources mention its importance but do not elaborate on specific matrix operations or concepts.
• Hermitian, Unitary, and Projection Operators
    ◦ These are specialized linear operators essential in quantum mechanics. The provided sources list them as topics but do not offer definitions or explanations of their properties or applications.
• Eigenvalues and Eigenvectors
    ◦ These concepts are applied to understand quantum mechanical problems involving linear operators.
    ◦ For the time-independent Schrödinger equation, the values of energy for which the equation can be solved are called energy Eigen-values, and their corresponding wave functions are called Eigen-functions. The equation is expressed as Hψ(x) = Eψ(x), where H is the Hamiltonian operator, and this is known as the eigen-value equation.
• Pauli Matrices
    ◦ Pauli matrices are 2x2 matrices that represent the spin components (Sₓ, Sᵧ, S₂) along three orthogonal axes.
    ◦ Wolfgang Pauli derived the equations associated with these matrices to describe the intrinsic angular momentum of electrons, known as spin.
    ◦ Measurements of spin components along any axis (e.g., z-direction) yield only two discrete outcomes: +ℏ/2 or -ℏ/2. These are referred to as spin up (|½⟩) and spin down (|½(-½)⟩) eigenstates.
    ◦ This demonstrates that spin is a quantized property and not derived from classical spinning motion.
• Commutation Relations
    ◦ For spin operators, specific commutation relations exist:
        ▪ [Sₓ, Sᵧ] = iℏS₂.
        ▪ [Sᵧ, S₂] = iℏSₓ.
        ▪ [S₂, Sₓ] = iℏSᵧ.
    ◦ Additionally, the total spin squared operator (S²) and the S₂ operator commute ([S², S₂] = 0), implying they share common eigenstates.