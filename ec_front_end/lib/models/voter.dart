class Voter {
  final int id;
  final String name;
  final String surname;
  final int ward;
  final String houseNo;
  final int age;
  final String? gender;
  final String? relation;
  final String? expectedParty;
  final String? occupation;
  final String? religion;
  final String? caste;
  final String? subCaste;
  final String? mobileNo;
  final String? voterStatus;

  Voter({
    required this.id,
    required this.name,
    required this.surname,
    required this.ward,
    required this.houseNo,
    required this.age,
    this.gender,
    this.relation,
    this.expectedParty,
    this.occupation,
    this.religion,
    this.caste,
    this.subCaste,
    this.mobileNo,
    this.voterStatus,
  });

  factory Voter.fromJson(Map<String, dynamic> json) {
    return Voter(
      id: json['voter_id'],
      name: json['name'],
      surname: json['surname'] ?? '',
      ward: json['ward'],
      houseNo: json['house_no'],
      age: json['age'],
      gender: json['gender'],
      relation: json['relation'],
      expectedParty: json['expected_party'],
      occupation: json['occupation'],
      religion: json['religion'],
      caste: json['caste'],
      subCaste: json['sub_caste'],
      mobileNo: json['mobile_no'],
      voterStatus: json['voter_status'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'voter_id': id,
      'name': name,
      'surname': surname,
      'ward': ward,
      'house_no': houseNo,
      'age': age,
      'gender': gender,
      'relation': relation,
      'expected_party': expectedParty,
      'occupation': occupation,
      'religion': religion,
      'caste': caste,
      'sub_caste': subCaste,
      'mobile_no': mobileNo,
      'voter_status': voterStatus,
    };
  }
}
