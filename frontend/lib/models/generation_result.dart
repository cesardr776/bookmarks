class GenerationResult {
  final String imageUrl;
  final String scenario;
  final String originalPrompt;

  const GenerationResult({
    required this.imageUrl,
    required this.scenario,
    required this.originalPrompt,
  });

  factory GenerationResult.fromJson(Map<String, dynamic> json) =>
      GenerationResult(
        imageUrl: json['image_url'] as String,
        scenario: json['scenario'] as String,
        originalPrompt: json['original_prompt'] as String,
      );
}
